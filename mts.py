import re
import requests
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import requests as rq
from os import getenv
from dotenv import load_dotenv
load_dotenv()

LOGIN = getenv("MTS_LOGIN")
PASSWORD = getenv("MTS_PASSWORD")
HISTORY_TIMEDELTA = 7  # days

requests = rq.Session()


class SSLAdapter(HTTPAdapter):
    """Custom Adapter to allow weak DH keys."""
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers("DEFAULT:@SECLEVEL=1")  # Lower security level
        kwargs["ssl_context"] = context
        super().init_poolmanager(*args, **kwargs)


requests.mount("https://", SSLAdapter())


def request_without_code():
    url = "https://vpbx.mts.ru/j_spring_security_check"
    headers = {
        "Host": "vpbx.mts.ru",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://vpbx.mts.ru",
        "Connection": "keep-alive",
        "Referer": "https://vpbx.mts.ru/login/;jsessionid=1ca8me55ibwii21ldbaokm1cg",
        "Cookie": "JSESSIONID=1ca8me55ibwii21ldbaokm1cg",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i"
    }
    data = {
        "j_username": LOGIN,
        "j_password": PASSWORD,
    }

    response = requests.post(url, headers=headers, data=data)

    print("Status Code:", response.status_code)
    print("Response Headers:", response.headers)
    print("Response Body:", response.text)


request_without_code()

def get_user_id():
    url = "https://vpbx.mts.ru/"

    headers = {
        "Host": "vpbx.mts.ru",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response text:", response.text)  # Print the response text (HTML or other content)
        match = re.search(r'/enterprise/(\d+)/', response.url)
        if match:
            enterprise_id = match.group(1)
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging

    return enterprise_id


user_id = get_user_id()


def get_gwt(user_id):
    url = "https://vpbx.mts.ru/vpbxGwt/vpbxGwt.nocache.js"

    headers = {
        "Host": "vpbx.mts.ru",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": f"https://vpbx.mts.ru/gwt/enterprise/{user_id}/",
        "Sec-Fetch-Dest": "script",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=2"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Request was successful!")
        print("JavaScript file saved as 'vpbxGwt.nocache.js'.")
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging

gwt = get_gwt(user_id)

def get_gwt2(user_id, gwt):
    url = f"https://vpbx.mts.ru/vpbxGwt/{gwt}.cache.js"

    headers = {
        "Host": "vpbx.mts.ru",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": f"https://vpbx.mts.ru/gwt/enterprise/{user_id}/",
        "Sec-Fetch-Dest": "script",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-origin"
    }

    # Send the GET request
    response = requests.get(url, headers=headers)

    # Check the response status code
    if response.status_code == 200:
        print("Request was successful!")
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging

gwt2 = get_gwt2(user_id, gwt)


def get_numbers_and_uuid():
    url = "https://vpbx.mts.ru/vpbxGwt/DispatcherGwtService"

    headers = {
        "Host": "vpbx.mts.ru",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "text/x-gwt-rpc; charset=utf-8",
        "X-GWT-Permutation": "4F3A39F8A8855D9244397AB61F97306B",
        "X-GWT-Module-Base": "https://vpbx.mts.ru/vpbxGwt/",
        "Content-Length": "244",
        "Origin": "https://vpbx.mts.ru",
        "Connection": "keep-alive",
        "Referer": "https://vpbx.mts.ru/gwt/enterprise/2613189773/othercrm/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    payload = "7|0|6|https://vpbx.mts.ru/vpbxGwt/|3945293F25DF8E22A327D69B6BEF95C5|ru.cti.vpbx.shared.services.DispatcherService|getForm|java.lang.Long/4227064769|ru.cti.vpbx.shared.services.DispatcherService$DISPATCHER/1933436215|1|2|3|4|2|5|6|5|CbwhyN|6|50|"

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging

number, number2, uuid = get_numbers_and_uuid()


def turn_on_api_methods(user_id):
    url = "https://vpbx.mts.ru/vpbxGwt/DispatcherGwtService"

    headers = {
        "Host": "vpbx.mts.ru",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "text/x-gwt-rpc; charset=utf-8",
        "X-GWT-Permutation": "4F3A39F8A8855D9244397AB61F97306B",
        "X-GWT-Module-Base": "https://vpbx.mts.ru/vpbxGwt/",
        "Origin": "https://vpbx.mts.ru",
        "Connection": "keep-alive",
        "Referer": f"https://vpbx.mts.ru/gwt/enterprise/{user_id}/othercrm/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0"
    }

    payload = (
        "7|0|12|https://vpbx.mts.ru/vpbxGwt/|3945293F25DF8E22A327D69B6BEF95C5|"
        "ru.cti.vpbx.shared.services.DispatcherService|updateForm|"
        "ru.cti.vpbx.shared.models.codebase.RecordGWTModel/4241958543|"
        "ru.cti.vpbx.shared.services.DispatcherService$DISPATCHER/1933436215|"
        "ru.cti.vpbx.shared.models.form.apicrm.OtherCrmFormGWTModel/1636192704|"
        "b92c9afa-3cfc-4ddf-8567-dad7c0f321e0|"
        "ru.cti.vpbx.shared.models.codebase.id.BlockIdGWTModel/1203261855|"
        "java.lang.Long/4227064769|https://callstata.ru/api/webhook/mts/12345||"
        "1|2|3|4|2|5|6|7|8|9|0|0|10|CbwhyN|11|12|1|10|CdI_zY|6|50|"
    )

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging

turn_on_api_methods(user_id)

























def start_session(self):
    if self.confirmation_code:
        self.request_with_code()
    else:
        self.request_without_code()


def add_webhook(self):
    self.start_session()
    try:
        self.create_new_token()
    except Exception:
        self.set_integration(api_enable=True)
        self.create_new_token()

    self.subscribe()

def delete_webhook(self):
    try:
        self.restore_session()
    except Exception:
        self.start_session()

    response_json = self.get_api_settings()
    if len(response_json["tokens"]) > 1:
        self.delete_token(response_json)
        return
    self.set_integration(api_enable=False)

    self.pbx_account.is_active = False
    self.pbx_account.save()

def add_phones(self):
    abonents_url = "https://cloudpbx.beeline.ru/apis/portal/abonents"
    abonents_headers = {"X-MPBX-API-AUTH-TOKEN": self.pbx_account.token}
    abonents_response = self.session.get(abonents_url, headers=abonents_headers)

    if abonents_response.status_code != 200:
        raise

    phones = []
    for item in abonents_response.json():
        phones.append(
            {
                "name": item.get("firstName", "") + " " + item.get("lastName", ""),
                "number": item["phone"],
                "login": item.get("extension"),
            }
        )
    # add_phones_to_db("number", self.pbx_account, phones)

def get_history(self):
    pass

def get_token(self):
    pass

def get_key(self):
    pass

def get_secret(self):
    pass

def get_url(self):
    pass

def get_previous_url(self):
    pass

# 5. Активация API
# активирует работу API и обнуляет ошибки доставки.
# • callbackUrl - URL для обратных вызовов (обязательный параметр)
# • clientApiKey - Ключ авторизации для обратного вызова (обязательный параметр)

def activate_api(uid, client_key):
    url = "https://vpbx.mts.ru/api/service/apicrm"

    payload = {
        "callbackUrl": f"https://callstata.ru/api/webhook/mts/{uid}",
        "clientApiKey": client_key,
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging


# choose one of activate
def activate_webhook(uid, client_key):
    url = "https://vpbx.mts.ru/api/service/webhook"

    payload = {
        "callbackUrl": f"https://callstata.ru/api/webhook/mts/{uid}",
        "clientApiKey": client_key,
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging


# CHECK_ALIVE указанный адресс в настройках. Если событие возвращает ответ не HTTP 200, то
# считаеся, что адрес не доступен


def get_abonents(token):
    url = "https://vpbx.mts.ru/api/abonents"

    headers = {
        "X-AUTH-TOKEN": token, # "Ваш токен скопированный из раздела 'Методы API'",
        "cache-control": "no-cache",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging

'''
[
{
"callingLineIdPhoneNumber": "string",
"department": "string",
"email": "string",
"extension": "string",
"firstName": "string",
"groupId": 0,
"lastname": "string",
"phoneNumber": "string",
"serviceProviderId": 0,
"userId": 0 }
]
где:
• serviceProviderId - идентификатор предприятия на портале vpbx
• groupId - идентификатор группы на портале vpbx
• userId - идентификатор абонента на портале vpbx
• firstName - имя абонента
• lastName - фамилия абонента
• phoneNumber - номер телефона абонента (MSIDN, используется только для мобильных
абонентов)
• extension - короткий номер
5 |
• callingLineIdPhoneNumber - АОН
• department - наименование подразделения
• email - адрес электронной почты абонента
'''

# параметры фильтрации истории вызовов передаются, как URL-переменные
# для фильтра используются следующие параметры:
# • direction - направление вызова, возможные значения ORIGINATING, TERMINATING
# • status - статус вызова, возможные значения PLACED, MISSED
# • calledNumber - номер с которого звонили
# • callingNumber - номер на который звонили
# • dateFrom - дата с, формат unixtimestamp, мс
# • dateTo - дата по, формат unixtimestamp, мс
# • page - страница
# • size - количество записей на странице
def get_history(token):
    url = "https://vpbx.mts.ru/api/v1/callHistory/enterprise"
    params = {
        "direction": "ORIGINATING",
        "status": "PLACED",
        "dateFrom": "1586250115000",
        "dateTo": "1586253915000",
        "page": "0",
        "size": "10"
    }

    headers = {
        "Content-Type": "application/json",
        "X-AUTH-TOKEN": token, #"Ваш токен скопированный из раздела 'Методы API'"
        "cache-control": "no-cache",
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging

'''
{
"content":
[
{
"enterpriseBwksId": "X214",
"groupBwksId": "X214G1",
"departmentBwksId": "",
"userId": "X214G1A2I@nvg.ru",
"callTime": 1558971019000,
"callingNumber": "202",
"calledNumber": "201",
"duration": 7,
"direction": "TERMINATING",
"status": "PLACED",
"answerDuration": 2,
"terminationCause": "NORMAL",
"redirectingNumber": "",
"redirectingReason": null,
"callGroupId": "148625",
"recordAbonentId": null,
"abonentName": null,
"timeZone": "GMT+03:00",
"extTrackingId": "21289855:1"
},
'''



def subscribe(token):
    # confirm that pbx_account is active
    url = "https://vpbx.mts.ru/api/subscription"

    headers = {
        "Content-Type": "application/json",
        "X-AUTH-TOKEN": token, # "Ваш токен скопированный из раздела 'Методы API'"
        "cache-control": "no-cache"
    }

    payload = {
        "abonentId": 1735
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging

'''
{
"expires": 0,
"subscriptionId": "string"
}
'''

def get_subscription(token, abonent_id, subscription_id):
    url = "https://vpbx.mts.ru/api/subscription"

    headers = {
        "Content-Type": "application/json",
        "X-AUTH-TOKEN": token, #"Ваш токен скопированный из раздела 'Методы API'"
        "cache-control": "no-cache"
    }

    payload = {
        "abonentId": abonent_id,
        "subscriptionId": subscription_id
    }

    response = requests.get(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging


def update_subscription(token ,abonent_id, subscription_id):
    url = "https://vpbx.mts.ru/api/subscription"

    headers = {
        "Content-Type": "application/json",
        "X-AUTH-TOKEN": token, #"Ваш токен скопированный из раздела 'Методы API'"
        "cache-control": "no-cache"
    }

    payload = {
        "abonentId": abonent_id,
        "subscriptionId": subscription_id
    }

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response JSON:", response.json())  # Print the response JSON if applicable
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging


# Возвращает файл записи разговора в том формате, который хранит система записи
# разговоров. extTrackingId - идентификатор разговора. Если записей разговоров больше чем
# одна запрашивать нужно по extTrackingId - callhalf
def get_record(token, extTrackingId, callhalf):
    url = f"https://vpbx.mts.ru/api/callRecording/{extTrackingId}:1callhalf-{callhalf}"

    headers = {
        "X-AUTH-TOKEN": token, # "Ваш токен скопированный из раздела 'Методы API'"
        "cache-control": "no-cache"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Request was successful!")
        if response.headers.get("Content-Type") == "audio/mpeg":
            with open("call_recording.mp3", "wb") as file:
                file.write(response.content)
            print("Call recording saved as 'call_recording.mp3'.")
        else:
            print("Response JSON:", response.json())
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging










