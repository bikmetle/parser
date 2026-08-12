import re
import requests
from bs4 import BeautifulSoup
from cookies import cookies
from headers import headers

class VacancyIdsNotFoundError(Exception):
    pass


headers_dict = {h["name"]: h["value"] for h in headers if h["name"] != "Cookie"}
cookies_dict = {c["name"]: c["value"] for c in cookies}

vacancy_ids = []
employer_ids = dict()


def get_employer_ids(html):
    soup = BeautifulSoup(html, "html.parser")
    ids = []
    seen_ids = set()

    for card in soup.select('div[id][class*="vacancy-card"]'):
        vacancy_id = card.get("id")

        employer_link = card.select_one('a[data-qa="vacancy-serp__vacancy-employer"]')
        if employer_link is None:
            continue

        employer_href = employer_link.get("href", "")
        if not isinstance(employer_href, str):
            continue

        match = re.search(r"/employer/(\d+)", employer_href)
        employer_id = match.group(1) if match else None

        if employer_id:
            employer_name = employer_link.get_text(" ", strip=True)
            employer_ids[employer_id] = employer_name

        if vacancy_id and vacancy_id not in seen_ids:
            seen_ids.add(vacancy_id)
            ids.append(vacancy_id)

    return ids

def get_vacancy_ids(page=None):
    base_url = "https://hh.ru/search/vacancy"
    params = {
        "enable_snippets": "false",
        "L_save_area": "true",
        "experience": "between3And6",
        "search_field": "name",
        "work_format": "REMOTE",
        "text": "python",
    }
    if page:
        params["page"] = page

    response = requests.get(base_url, params=params, headers=headers_dict, cookies=cookies_dict)

    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)}")

    ids = get_employer_ids(response.text)
    print(f"Found {len(ids)} vacancies:")

    if not ids:
        raise VacancyIdsNotFoundError

    return ids


for i in range(10):
    try:
        vacancy_ids.extend(get_vacancy_ids(i))
    except VacancyIdsNotFoundError:
        break


session = requests.Session()

print(employer_ids)
