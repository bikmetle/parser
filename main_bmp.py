import os
import logging
import json
import sys
import asyncio
import aioconsole

from browsermobproxy import Server
from selenium import webdriver
from contextlib import contextmanager
from decode_entry import decode_response_content
from selenium.webdriver.firefox.service import Service
logging.basicConfig(level=logging.INFO)

root = os.path.dirname(__file__)


@contextmanager
def firefox_session():
    server = Server(f"{root}/browsermob-proxy/bin/browsermob-proxy")
    server.start()

    browsermobproxy = server.create_proxy()
    webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
        "proxyType": "manual",
        'httpProxy': browsermobproxy.selenium_proxy().http_proxy,
        'sslProxy': browsermobproxy.selenium_proxy().ssl_proxy,
    }
    geckodriver_path = "/snap/bin/geckodriver"
    driver_service = Service(executable_path=geckodriver_path)
    
    driver = webdriver.Firefox(service=driver_service)

    browsermobproxy.new_har("init_label", options={"captureHeaders": True, 
                                                   "captureContent": True, 
                                                   "captureBinaryContent": True})

    try:
        logging.info("Start new firefox session.")
        yield driver, browsermobproxy
    finally:
        server.stop()
        driver.quit()
        logging.info("Stop the firefox session.")


def create_project_dir(project_name):
    try:
        project_dir = f"{project_name}_p"
        os.mkdir(project_dir)
    except OSError as error:
        print(f"Failed to create folder: {error}")

    return project_dir


def create_label_dir(project_dir, label):
    try:
        label_dir = f"{project_dir}/{label}"
        os.mkdir(label_dir)
    except OSError as error:
        print(f"Failed to create folder: {error}")

    return label_dir


def create_project():
    project_name = input("Enter your project name (type 'exit' to quit): ").strip().lower()

    if project_name == 'exit':
        print("Exiting program...")
        sys.exit()
    else:
        project_dir = create_project_dir(project_name)
    return project_dir


async def sub_task(queue):
    item = await asyncio.wait_for(queue.get(), timeout=1)
    browsermobproxy, label_dir, new_label = item

    while True:
        entry_count = 0
        entries = browsermobproxy.har['log']['entries']
        browsermobproxy.new_har(new_label, options={"captureHeaders": True, 
                                            "captureContent": True, 
                                            "captureBinaryContent": True})
        for entry in entries:
            entry_count += 1
            file = f"{label_dir}/{entry_count}.json"
            if os.path.exists(file):
                continue
            if entry['response']['content'].get("mimeType") == "application/json; charset=utf-8" and entry['response']['content'].get("encoding") == "base64":
                entry['response']['content']['text'] = decode_response_content(entry['response']['content']['text'])
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=4)

        try:
            item = await asyncio.wait_for(queue.get(), timeout=1)
            browsermobproxy, label_dir, new_label = item

            if new_label == 'exit':
                print("Exiting program...")
                break

        except TimeoutError:
            pass


async def main_task(queue):
    with firefox_session() as (driver, browsermobproxy):
        project_dir = create_project()
        label = "0_init"
        label_dir = create_label_dir(project_dir, label)
        await queue.put((browsermobproxy, label_dir, label))

        label_count = 0
        while True:
            label = await aioconsole.ainput("Enter new label, the previous will be saved (type 'exit' to quit): ")
            label = label.strip().lower()
            if label == 'exit':
                print("Exiting program...")
                await queue.put((browsermobproxy, label_dir, label))
                break
            else:
                label_count += 1
                label_dir = create_label_dir(project_dir, f"{label_count}_{label}")
                await queue.put((browsermobproxy, label_dir, label))


async def main():
    queue = asyncio.Queue()
    await asyncio.gather(main_task(queue), sub_task(queue))

asyncio.run(main())
