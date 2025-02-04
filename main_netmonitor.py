from contextlib import contextmanager
from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from urls_to_skip import urls_to_skip
import json
import logging
import os
import time
import subprocess
from urllib.parse import urlparse


logging.basicConfig(level=logging.INFO)

root = os.path.dirname(__file__)

url='https://hackerone.com/directory/programs?offers_bounties=true&order_direction=DESC&order_field=launched_at'
hostname = urlparse(url).hostname.split('.')[0]
cookies_file = f"cookies/{hostname}.json"
is_tunnel_enabled = False


def start_ssh_tunnel():
    try:
        command = ["ssh", "call", "-fN", "-D", "1080"]
        subprocess.run(command, check=True)
        logging.info("SSH command executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.info(f"An error occurred while executing the SSH command: {e}")
    except Exception as e:
        logging.info(f"Unexpected error: {e}")

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
        logging.info("Start new firefox session.")
        yield driver
    finally:
        driver.quit()
        logging.info("Stop the firefox session.")


def saveCookies(driver):
    cookies = driver.get_cookies()

    with open(cookies_file, 'w') as file:
        json.dump(cookies, file)
    logging.info('New Cookies saved successfully')


def loadCookies():
    if cookies_file in os.listdir():
        with open(cookies_file, 'r') as file:
            cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    else:
        logging.info('No cookies file found')
    
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

        file = f"sites/{project_name}/{entry['startedDateTime']}.json"
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=4)

    logging.info(f"{len(har_data['entries'])} requests saved")


with selenium_driver() as driver:
    if is_tunnel_enabled:
        start_ssh_tunnel()
    driver.get(url)
    loadCookies()

    project_name = input("Enter the project name or `exit`: ")
    saveCookies(driver)

    if project_name != 'exit':
        try:
            project_dir = f"sites/{project_name}"
            os.mkdir(project_dir)
        except OSError as error:
            logging.info(f"Failed to create folder: {error}")

        driver.install_addon("har-export-trigger.zip", temporary=True)
        har_data = get_har_data()
        save_har_data(har_data)
