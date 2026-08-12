from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import JavascriptException, NoSuchDriverException
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from urls_to_skip import urls_to_skip
import json
import os
import platform
import shutil
import time
import subprocess
import tarfile
import tempfile
import zipfile
from urllib.parse import urlparse
from loguru import logger
import requests

url = input("\nPlease enter the URL: ")
project_name = input("Enter the project name to save or type `exit`: ")

root = os.path.dirname(__file__)

parsed_url = urlparse(url)
hostname = ".".join(parsed_url.hostname.split(".")[:-1])
cookies_file = f"cookies/{hostname}.json"
is_tunnel_enabled = False


def download_geckodriver() -> Path:
    """Download the latest geckodriver release and return its local path."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        asset_platform = "linux-aarch64" if machine in {"aarch64", "arm64"} else "linux64"
    elif system == "darwin":
        asset_platform = "macos-aarch64" if machine in {"aarch64", "arm64"} else "macos"
    elif system == "windows":
        asset_platform = "win-aarch64" if machine in {"aarch64", "arm64"} else "win64"
    else:
        raise RuntimeError(f"Unsupported platform for geckodriver: {system}/{machine}")

    driver_name = "geckodriver.exe" if system == "windows" else "geckodriver"
    driver_path = Path(root) / ".drivers" / driver_name
    if driver_path.is_file():
        return driver_path

    driver_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading geckodriver for {asset_platform}...")
    release_response = requests.get(
        "https://api.github.com/repos/mozilla/geckodriver/releases/latest",
        headers={"Accept": "application/vnd.github+json"},
        timeout=30,
    )
    release_response.raise_for_status()
    assets = release_response.json()["assets"]
    asset = next(
        (
            item
            for item in assets
            if asset_platform in item["name"]
            and item["name"].endswith((".tar.gz", ".zip"))
        ),
        None,
    )
    if asset is None:
        raise RuntimeError(f"No geckodriver release found for {asset_platform}")

    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / asset["name"]
        with requests.get(asset["browser_download_url"], stream=True, timeout=120) as response:
            response.raise_for_status()
            with archive_path.open("wb") as archive_file:
                shutil.copyfileobj(response.raw, archive_file)

        if archive_path.name.endswith(".zip"):
            with zipfile.ZipFile(archive_path) as archive:
                with archive.open(driver_name) as source, driver_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
        else:
            with tarfile.open(archive_path, "r:gz") as archive:
                member = archive.getmember(driver_name)
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError("geckodriver binary is missing from the archive")
                with source, driver_path.open("wb") as target:
                    shutil.copyfileobj(source, target)

    driver_path.chmod(0o755)
    logger.info(f"Geckodriver installed at {driver_path}")
    return driver_path


def start_ssh_tunnel():
    try:
        command = ["ssh", "call", "-fN", "-D", "1080"]
        subprocess.run(command, check=True)
        logger.info("SSH command executed successfully.")
    except subprocess.CalledProcessError as e:
        logger.info(f"An error occurred while executing the SSH command: {e}")
    except Exception as e:
        logger.info(f"Unexpected error: {e}")

@contextmanager
def selenium_driver():
    options=Options()
    
    if is_tunnel_enabled:
        start_ssh_tunnel()
        firefox_profile = FirefoxProfile("/home/bikmetle/.mozilla/firefox/699rashk.default-release")
    else:
        firefox_profile = FirefoxProfile("/home/bikmetle/.mozilla/firefox/8cqvs1rn.default-1762880211570")

    options.add_argument("--devtools")   
    firefox_profile.set_preference("devtools.toolbox.selectedTool", "netmonitor")
    firefox_profile.set_preference("devtools.netmonitor.persistlog", True)
    firefox_profile.set_preference("browser.cache.disk.enable", False)
    firefox_profile.set_preference("browser.cache.memory.enable", False)
    firefox_profile.set_preference("browser.cache.offline.enable", False)
    firefox_profile.set_preference("network.http.use-cache", False)
    options.profile = firefox_profile
    geckodriver_path = Path("/usr/local/bin/geckodriver")
    try:
        driver = webdriver.Firefox(
            service=Service(executable_path=str(geckodriver_path)),
            options=options,
        )
    except NoSuchDriverException:
        logger.warning(f"Geckodriver was not found at {geckodriver_path}")
        geckodriver_path = download_geckodriver()
        driver = webdriver.Firefox(
            service=Service(executable_path=str(geckodriver_path)),
            options=options,
        )

    try:
        logger.info("Start new firefox session.")
        yield driver
    finally:
        driver.quit()
        logger.info("Stop the firefox session.")


def get_har_data(attempt=0):
    if attempt > 10:
        raise

    attempt += 1
    logger.info(f"Get har data attempt {attempt}")
    logger.info(f"Waiting for {attempt*2} seconds")
    time.sleep(attempt*2)

    try:
        har_data = driver.execute_async_script(
            "HAR.triggerExport().then(arguments[0]);"
        )
    except JavascriptException:
        logger.info("JavascriptException occurred")
        return get_har_data(attempt)

    return har_data


def save_har_data(har_data, steps):
    dict_iterator = iter(steps.items())
    step_datetime, step_name = next(dict_iterator)
    entry_count = 0
    for entry in har_data['entries']:
        entry_count += 1

        if any(url in entry['request']['url'] for url in urls_to_skip):
            continue

        started_datetime = datetime.fromisoformat(entry['startedDateTime']).astimezone(timezone.utc)

        if step_datetime < started_datetime:
            step_datetime, step_name = next(dict_iterator)
        # step_dir = f"har_data/{project_name}/{entry_count}_{step_name}"
        # if not os.path.exists(step_dir):
        #     os.makedirs(step_dir)
        file = f"har_data/{project_name}/{entry['startedDateTime'][11:23]}_{step_name}.json"
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=4)

    logger.info(f"{len(har_data['entries'])} requests saved")


with selenium_driver() as driver:
    driver.get(url)
    steps = dict()
    steps[datetime.now(timezone.utc)] = "init"

    while True:
        step = input("Enter the previous step name: ")
        if step == "exit":
            break
        steps[datetime.now(timezone.utc)] = step

    if project_name != 'exit':
        if not os.path.exists("har_data"):
            os.mkdir("har_data")

        if not os.path.exists(f"har_data/{project_name}"):
            os.mkdir(f"har_data/{project_name}")

        driver.install_addon("har-export-trigger.zip", temporary=True)
        har_data = get_har_data()
        steps[datetime.now(timezone.utc)] = "end"
        save_har_data(har_data, steps)




    # for name, value in cookies_dict.items():
    #     try:
    #         driver.add_cookie({
    #             'name': name,
    #             'value': value,
    #             'domain': urlparse(driver.current_url).hostname
    #         })
    #     except Exception as e:
    #         logger.warning(f"Failed to add cookie {name}: {e}")
