import asyncio
import json
import re
from collections import Counter
import aiohttp
import requests
from bs4 import BeautifulSoup
from cookies import cookies
from headers import headers

class VacancyIdsNotFoundError(Exception):
    pass

headers_dict = {h["name"]: h["value"] for h in headers if h["name"] != "Cookie"}
cookies_dict = {c["name"]: c["value"] for c in cookies}

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


async def get_vacancy_data(session, vacancy_id):
    base_url = f"https://hh.ru/vacancy/{vacancy_id}"
    params = {
        "query": "python developer",
        "hhtmFrom": "vacancy_search_list",
    }
    async with session.get(base_url, params=params, headers=headers_dict, cookies=cookies_dict) as response:
        text = await response.text()
    print(f"Vacancy {vacancy_id} data fetched")
    # Parse HTML and find JSON-LD script
    soup = BeautifulSoup(text, 'lxml')
    script_tag = soup.find('script', type='application/ld+json')
    
    if not script_tag:
        return Counter()
    
    job_data = json.loads(script_tag.string)
    description_html = job_data.get('description', '')
    
    # Strip HTML tags from description
    description_soup = BeautifulSoup(description_html, 'lxml')
    description_text = description_soup.get_text(separator=' ')
    
    # Clean and split into words (only alphabetic words)
    words = re.findall(r'[a-zA-Z0-9]+', description_text.lower())
    
    # Count words
    return Counter(words)

async def fetch_all_vacancy_data(vacancy_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [get_vacancy_data(session, vid) for vid in vacancy_ids]
        results = await asyncio.gather(*tasks)
    return results


async def main():
    total_word_count = Counter()
    
    for i in range(10):
        try:
            vacancy_ids.extend(get_vacancy_ids(i))
        except VacancyIdsNotFoundError:
            break
    
    # Fetch all vacancy data concurrently
    word_counts = await fetch_all_vacancy_data(vacancy_ids)
    
    for word_count in word_counts:
        total_word_count += word_count
    
    print(f"Total unique words: {len(total_word_count)}")
    print("Top 100 words:", total_word_count.most_common(100))


if __name__ == "__main__":
    asyncio.run(main())
