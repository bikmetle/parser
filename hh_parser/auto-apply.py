import json
import os
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from cookies import cookies
from headers import headers

class VacancyIdsNotFoundError(Exception):
    pass

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

headers_dict = {h["name"]: h["value"] for h in headers if h["name"] != "Cookie"}
cookies_dict = {c["name"]: c["value"] for c in cookies}
RESUME_HASH = os.getenv("HH_RESUME_HASH", "64931b3aff0e1f688b0039ed1f4d3754636371")

vacancy_ids = []

def get_vacancy_ids(page=None):
    base_url = "https://hh.ru/search/vacancy"
    params = {
        "enable_snippets": "false",
        "L_save_area": "true",
        "experience": "between3And6",
        "search_field": "name",
        "work_format": "REMOTE",
        "text": "python developer",
    }
    if page:
        params["page"] = page

    response = requests.get(base_url, params=params, headers=headers_dict, cookies=cookies_dict)

    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)}")

    ids = re.findall(r'"vacancyId":(\d+)', response.text)
    ids = list(set(ids))  # Remove duplicates
    print(f"Found {len(ids)} unique vacancy IDs:")

    if not ids:
        raise VacancyIdsNotFoundError

    return ids


def get_vacancy_description(session, vacancy_id):
    base_url = f"https://hh.ru/vacancy/{vacancy_id}"
    params = {
        "query": "python developer",
        "hhtmFrom": "vacancy_search_list",
    }
    response = session.get(base_url, params=params, headers=headers_dict, cookies=cookies_dict)
    text = response.text
    print(f"Vacancy {vacancy_id} data fetched")

    # Parse HTML and find JSON-LD script
    soup = BeautifulSoup(text, "html.parser")
    script_tag = soup.find('script', type='application/ld+json')
    
    if not script_tag:
        return ""
    
    job_data = json.loads(script_tag.string)
    description_html = job_data.get('description', '')
    
    # Strip HTML tags from description
    description_soup = BeautifulSoup(description_html, "html.parser")
    description_text = description_soup.get_text(separator=' ')
    
    return description_text


def read_cv():
    cv_path = BASE_DIR / "cv-ru.txt"
    return cv_path.read_text(encoding="utf-8")


def make_cover_letter(cv_text, vacancy_description):
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        instructions=(
            "You write concise, natural Russian cover letters for hh.ru job applications. "
            "Use only facts from the CV. Match the candidate's skills to the vacancy. "
            "Do not invent experience, companies, education, salary, or availability. "
            "Keep it professional, friendly, and under 180 words."
        ),
        input=f"""
CV:
{cv_text}

Vacancy description:
{vacancy_description}

Write a personalized cover letter in Russian. Mention the strongest matching skills.
""".strip(),
    )
    return response.output_text.strip()


def make_apply_headers(vacancy_id):
    xsrf_token = cookies_dict.get("_xsrf", "")
    return {
        "Accept": "application/json",
        "User-Agent": headers_dict.get("User-Agent", ""),
        "X-hhtmSource": "vacancy",
        "X-hhtmFrom": "vacancy_search_list",
        "X-Requested-With": "XMLHttpRequest",
        "X-Xsrftoken": xsrf_token,
        "X-GIB-GSSCgib-w-hh": cookies_dict.get("gsscgib-w-hh", ""),
        "X-GIB-FGSSCgib-w-hh": cookies_dict.get("fgsscgib-w-hh", ""),
        "Origin": "https://hh.ru",
        "Referer": (
            f"https://hh.ru/vacancy/{vacancy_id}"
            "?query=python+developer&hhtmFrom=vacancy_search_list"
        ),
    }


def apply_to_vacancy(session, vacancy_id, cover_letter):
    url = "https://hh.ru/applicant/vacancy_response/popup"
    xsrf_token = cookies_dict.get("_xsrf", "")
    fields = {
        "_xsrf": xsrf_token,
        "vacancy_id": str(vacancy_id),
        "resume_hash": RESUME_HASH,
        "ignore_postponed": "true",
        "incomplete": "false",
        "mark_applicant_visible_in_vacancy_country": "false",
        "country_ids": "[]",
        "letter": cover_letter,
        "lux": "true",
        "withoutTest": "no",
        "hhtmFromLabel": "",
        "hhtmSourceLabel": "",
    }
    files = {name: (None, value) for name, value in fields.items()}

    response = session.post(
        url,
        files=files,
        headers=make_apply_headers(vacancy_id),
        cookies=cookies_dict,
        timeout=30,
    )

    if response.status_code != 200:
        print(f"Apply failed for vacancy {vacancy_id}: {response.status_code}")
        print(response.text[:100])
        return False

    print(f"Applied to vacancy {vacancy_id}")
    return True


for i in range(10):
    try:
        vacancy_ids.extend(get_vacancy_ids(i))
    except VacancyIdsNotFoundError:
        break

cv_text = read_cv()

session = requests.Session()
for vid in vacancy_ids:
    vacancy_description = get_vacancy_description(session, vid)
    cover_letter = make_cover_letter(cv_text, vacancy_description)
    print(f"\nCover letter for vacancy {vid}:\n{cover_letter}\n")

    apply_to_vacancy(session, vid, cover_letter)
