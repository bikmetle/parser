import asyncio
import re
import aiohttp
import requests
from cookies import cookies
from headers import headers
from respond_c_h import respond_headers, respond_cookies

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


async def respond_to_vacancy(session, vacancy_id):
    headers_dict = {h["name"]: h["value"] for h in respond_headers if h["name"] != "Cookie"}
    cookies_dict = {c["name"]: c["value"] for c in respond_cookies}
    
    base_url = "https://hh.ru/applicant/vacancy_response/popup"
    
    # Build multipart form data
    data = aiohttp.FormData()
    data.add_field("resume_hash", "64931b3aff0e1f688b0039ed1f4d3754636371")
    data.add_field("vacancy_id", str(vacancy_id))
    data.add_field("letterRequired", "false")
    data.add_field("lux", "true")
    data.add_field("ignore_postponed", "true")
    data.add_field("mark_applicant_visible_in_vacancy_country", "false")
    data.add_field("country_ids", "[]")

    async with session.post(base_url, data=data, headers=headers_dict, cookies=cookies_dict) as response:
        text = await response.text()
        status = response.status

    if status != 200:
        print(f"Error responding to vacancy {vacancy_id}: {text}")
    else:
        print(f"Responded to vacancy {vacancy_id}")


async def respond_to_all_vacancies(vacancy_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [respond_to_vacancy(session, vid) for vid in vacancy_ids]
        results = await asyncio.gather(*tasks)
    return results


async def main():
    # for i in range(10):
    #     try:
    #         vacancy_ids.extend(get_vacancy_ids(i))
    #     except VacancyIdsNotFoundError:
    #         break
    vacancy_ids = ['129480031', '129288224', '129545663', '129609351', '129503025', '129809855', '129606201', '122535294', '129818433', '129808485', '129701567', '129590292', '129530118', '129610881', '129533779', '129354443', '129310195', '129720331', '129435547', '129446091', '129615432', '129590291', '129343483', '129672232', '129698414', '129717869', '129394039', '129815486', '129791677', '129384414', '129801593', '129589230', '129647061', '129813214', '129622632', '129594341', '129395822', '129713934', '129511481', '129594163', '129352952', '129718696', '129768454', '129724365', '129668514', '129717671', '129790964', '129715340', '127533415', '128942243', '129805654', '128465804', '129340740', '129316683', '128691661', '129689143', '129666858', '129440300', '129694205', '128099946', '123450217', '129232923', '129395329', '126738424', '129530321', '129562480', '129689141', '129671169', '125404032', '129006385', '129303418', '129615569', '127350566', '129252732', '129458993', '129226259', '129748165', '129293696', '129104674', '128691660', '129608812', '129491194', '129275087', '129504215', '129689142', '129318858', '129810683', '129284331', '129337605', '129540473', '129237566', '129435735', '126073718', '129489419', '129367881', '129718457', '129576166', '124463631', '129360735', '129487640', '129156324', '129262717', '128667131', '127642557', '129223717', '128958487', '123440677', '127533413', '129198427', '127533414', '127384157', '128514244', '129175240', '128790420', '128816653', '128833799', '129690525', '126825379', '126811357', '129442486', '129228338', '129149579', '129323387', '129196502', '129169546', '128587419', '129169589', '129152022', '127872471']
    print(f"Responding to {len(vacancy_ids)} vacancies")
    print(vacancy_ids)
    # Fetch all vacancy data concurrently
    await respond_to_all_vacancies(vacancy_ids)
    

if __name__ == "__main__":
    asyncio.run(main())
