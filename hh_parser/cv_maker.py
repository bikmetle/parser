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

vacancy_ids = []
employer_ids = dict()

def get_applicable_vacancy_ids(html):
    soup = BeautifulSoup(html, "html.parser")
    ids = []
    seen_ids = set()

    for card in soup.select('div[id][class*="vacancy-card"]'):
        vacancy_id = card.get("id")

        employer_link = card.select_one('a[data-qa="vacancy-serp__vacancy-employer"]')
        employer_href = employer_link.get("href", "")

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
        "text": "python developer",
        # "text": "python разработчик",
        # TODO: посмотреть на ютубе видео как составлять резюме
    }
    if page:
        params["page"] = page

    response = requests.get(base_url, params=params, headers=headers_dict, cookies=cookies_dict)

    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)}")

    ids = get_applicable_vacancy_ids(response.text)
    print(f"Found {len(ids)} vacancies with Откликнуться:")

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

    descriptions_path = BASE_DIR / "descriptions.txt"
    with descriptions_path.open("a", encoding="utf-8") as file:
        file.write(description_text + "\n")
        
    return description_text


def read_cv():
    cv_path = BASE_DIR / "cv-ru.txt"
    return cv_path.read_text(encoding="utf-8")


def read_descriptions():
    descriptions_path = BASE_DIR / "descriptions.txt"
    return descriptions_path.read_text(encoding="utf-8")


def make_cv(cv_text, descriptions_text):
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        instructions=(
            "You rewrite Russian CVs for hh.ru job applications based on vacancy descriptions. "
            "Make the CV clear for recruiters and ATS/AI screening: use relevant keywords from "
            "the vacancies naturally, keep section names obvious, and put the strongest matches "
            "near the top. Write in professional, human-sounding Russian without inflated buzzwords. "
            "Add measurable achievements; phrase them as concrete results, for example performance "
            "improvements, saved money, reduced manual work, faster delivery, or reliability gains. "
            "Include that the applicant has experience from the pre-AI-tools era, can write code "
            "with or without AI assistants, and can work effectively with Cursor and similar tools. "
            "Keep the CV concise, credible, and tailored to Python developer roles."
        ),
        input=f"""
Original CV:
{cv_text}

Vacancy descriptions:
{descriptions_text}

Applicant notes:
- Mention that I started coding before AI coding tools were common.
- Mention that I can write code independently without AI tools and also use AI tools effectively.
- Mention that I can work with Cursor and similar AI-assisted coding tools.
- Add measurable achievements such as about 10% performance improvement,
  large cost savings in roubles, reduced manual work, faster delivery, improved reliability.

Rewrite the CV in Russian for these vacancies. Keep it suitable for hh.ru and AI/ATS filters.
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


for i in range(10):
    try:
        vacancy_ids.extend(get_vacancy_ids(i))
    except VacancyIdsNotFoundError:
        break


session = requests.Session()
for vid in vacancy_ids:
    vacancy_description = get_vacancy_description(session, vid)

cv_text = read_cv()
descriptions_text = read_descriptions()
cv = make_cv(cv_text, descriptions_text)
print("\nCV for vacancies is ready")


print(employer_ids)
