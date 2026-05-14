import requests

from cookies import cookies
from headers import headers

url = "https://disk.yandex.ru/d/xuIJNMNfL5oOOA"

# Build dicts for requests (name -> value); use Cookie from cookies.py only
headers_dict = {h["name"]: h["value"] for h in headers if h["name"] != "Cookie"}
cookies_dict = {c["name"]: c["value"] for c in cookies}

# response = requests.get(url, headers=headers_dict, cookies=cookies_dict)
response = requests.get(url, cookies=cookies_dict)
response.raise_for_status()

print(response.status_code)
print(response.text[:1000] if response.text else "")
