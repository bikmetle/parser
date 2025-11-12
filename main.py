from contextlib import contextmanager
from datetime import datetime, timezone
from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from urls_to_skip import urls_to_skip
import json
import os
import time
import subprocess
from urllib.parse import urlparse
from loguru import logger

url = input("\nPlease enter the URL: ")
project_name = input("Enter the project name to save or type `exit`: ")

root = os.path.dirname(__file__)

parsed_url = urlparse(url)
hostname = ".".join(parsed_url.hostname.split(".")[:-1])
cookies_file = f"cookies/{hostname}.json"
is_tunnel_enabled = False


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
        firefox_profile = FirefoxProfile("/home/bikmetle/.mozilla/firefox/dlvoc3tb.default")

    options.add_argument("--devtools")   
    firefox_profile.set_preference("devtools.toolbox.selectedTool", "netmonitor")
    firefox_profile.set_preference("devtools.netmonitor.persistlog", True)
    firefox_profile.set_preference("browser.cache.disk.enable", False)
    firefox_profile.set_preference("browser.cache.memory.enable", False)
    firefox_profile.set_preference("browser.cache.offline.enable", False)
    firefox_profile.set_preference("network.http.use-cache", False)
    options.profile = firefox_profile
    geckodriver_path = "/usr/local/bin/geckodriver"
    driver_service = Service(executable_path=geckodriver_path)

    driver = webdriver.Firefox(
        service=driver_service,
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
        file = f"har_data/{project_name}/{entry['startedDateTime'][11:]}_{step_name}.json"
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=4)

    logger.info(f"{len(har_data['entries'])} requests saved")


with selenium_driver() as driver:
    driver.get(url)
    steps = dict()
    steps[datetime.now(timezone.utc)] = "init"

    while True:
        step = input("Enter the step name: ")
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
