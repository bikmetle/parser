from contextlib import contextmanager
import json
import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import JavascriptException
from urls_to_skip import urls_to_skip

logging.basicConfig(level=logging.INFO)


@contextmanager
def selenium_driver():
    options=Options()
    firefox_profile = FirefoxProfile("/home/bikmetle/.mozilla/firefox/699rashk.default-release")
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

    with open('cookies.json', 'w') as file:
        json.dump(cookies, file)
    logging.info('New Cookies saved successfully')


def loadCookies():
    if 'cookies.json' in os.listdir():
        with open('cookies.json', 'r') as file:
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

        file = f"{project_name}_p/{entry['startedDateTime']}.json"
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=4)

    logging.info(f"{len(har_data['entries'])} requests saved")


with selenium_driver() as driver:
    driver.get("https://lk.mango-office.ru")
    loadCookies()

    project_name = input("Enter the project name or `exit`: ")
    saveCookies(driver)

    if project_name != 'exit':
        try:
            project_dir = f"{project_name}_p"
            os.mkdir(project_dir)
        except OSError as error:
            logging.info(f"Failed to create folder: {error}")

        driver.install_addon("har-export-trigger.zip", temporary=True)
        har_data = get_har_data()
        save_har_data(har_data)
