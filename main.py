from contextlib import contextmanager
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
# from urls import URLS

url = input("\nPlease enter the URL: ")
logger.info("Starting firefox session.")

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
        firefox_profile = FirefoxProfile("/home/bikmetle/.mozilla/firefox/699rashk.default-release")
    else:
        firefox_profile = FirefoxProfile("/home/bikmetle/.mozilla/firefox/dlvoc3tb.default")

    options.add_argument("--devtools")   
    firefox_profile.set_preference("devtools.toolbox.selectedTool", "netmonitor")
    firefox_profile.set_preference("devtools.netmonitor.persistlog", True)
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


def saveCookies(driver):
    cookies = driver.get_cookies()

    with open(cookies_file, 'w') as file:
        json.dump(cookies, file)
    logger.info('New Cookies saved successfully')


def loadCookies():
    dir_name, file_name = cookies_file.split("/")
    if file_name in os.listdir(dir_name):
        with open(cookies_file, 'r') as file:
            cookies = json.load(file)
        for cookie in cookies:
            parsed_url = urlparse(driver.current_url)
            domain = ".".join(parsed_url.hostname.split(".")[-2:])
            cookie['domain']="."+domain
            driver.add_cookie(cookie)
    else:
        logger.info('No cookies file found')
    
    driver.refresh() # Refresh Browser after login


def get_har_data(attempt=0):
    if attempt > 10:
        raise

    attempt += 1
    time.sleep(attempt*2)

    try:
        har_data = driver.execute_async_script(
            "HAR.triggerExport().then(arguments[0]);"
        )
    except JavascriptException:
        return get_har_data(attempt)

    return har_data


def save_har_data(har_data):
    entry_count = 0
    for entry in har_data['entries']:
        entry_count += 1

        if any(url in entry['request']['url'] for url in urls_to_skip):
            continue

        file = f"har_data/{project_name}/{entry['startedDateTime']}.json"
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=4)

    logger.info(f"{len(har_data['entries'])} requests saved")


with selenium_driver() as driver:
    if is_tunnel_enabled:
        start_ssh_tunnel()
    driver.get(url)
    loadCookies()
    driver.get(url)

    project_name = input("Enter the project name to save or type `exit`: ")
    saveCookies(driver)

    if project_name != 'exit':
        try:
            project_dir = f"har_data/{project_name}"
            os.mkdir(project_dir)
        except OSError as error:
            logger.info(f"Failed to create folder: {error}")

        driver.install_addon("har-export-trigger.zip", temporary=True)
        har_data = get_har_data()
        save_har_data(har_data)
