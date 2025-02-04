import requests as rq
requests = rq.Session()
HISTORY_TIMEDELTA = 7  # days


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
        "Referer": "https://vpbx.mts.ru/login/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i"
    }

    data = {
    }

    response = requests.post(url, headers=headers, data=data)

    print("Status Code:", response.status_code)
    print("Response Headers:", response.headers)
    print("Response Body:", response.text)


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
