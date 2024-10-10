import json
import os
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import JavascriptException
from urls_to_skip import urls_to_skip


def save_cookies(driver, path):
    with open(path, 'w') as file:
        json.dump(driver.get_cookies(), file)

def load_cookies(driver, path):
    with open(path, 'r') as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)


options=Options()
# firefox_profile = FirefoxProfile()
firefox_profile = FirefoxProfile("/home/bikmetle/.mozilla/firefox/699rashk.default-release")
options.add_argument("--devtools")   
firefox_profile.set_preference("devtools.toolbox.selectedTool", "netmonitor")
firefox_profile.set_preference("devtools.netmonitor.persistlog", True)
options.profile = firefox_profile
geckodriver_path = "/usr/local/bin/geckodriver"
driver_service = Service(executable_path=geckodriver_path)

browser = webdriver.Firefox(
    service=driver_service,
    options=options,
)
load_cookies(browser, "cookies.txt")

# record interesting stuff
...

project_name = input("Enter the project name: ")
try:
    project_dir = f"{project_name}_p"
    os.mkdir(project_dir)
except OSError as error:
    print(f"Failed to create folder: {error}")

browser.install_addon("har-export-trigger.zip", temporary=True)


def get_har_data(seconds=1):
    time.sleep(seconds)
    try:
        har_data = browser.execute_async_script(
            "HAR.triggerExport().then(arguments[0]);"
        )
    except JavascriptException:
        seconds *= 2 
        return get_har_data(seconds)
    return har_data

har_data = get_har_data()

save_cookies(browser, "cookies.txt")
browser.quit()


entry_count = 0
for entry in har_data['entries']:
    entry_count += 1

    if any(url in entry['request']['url'] for url in urls_to_skip):
        continue

    file = f"{project_name}_p/{entry['startedDateTime']}.json"
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(entry, f, ensure_ascii=False, indent=4)


print(f"{len(har_data['entries'])} requests saved")
