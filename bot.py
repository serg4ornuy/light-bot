import requests
import hashlib
import os

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

CITY = "Богуслав"
STREET = "Росьова"
HOUSE = "70"


session = requests.Session()


def get_address_id():

    url = "https://www.dtek-krem.com.ua/api/location/search"

    params = {
        "q": f"{CITY} {STREET} {HOUSE}"
    }

    r = session.get(url, params=params, timeout=30)

    if r.status_code != 200:
        return None

    data = r.json()

    if not data:
        return None

    return data[0]["id"]


def get_schedule(address_id):

    url = f"https://www.dtek-krem.com.ua/api/shutdowns/address/{address_id}"

    r = session.get(url, timeout=30)

    if r.status_code != 200:
        return None

    return r.text


def send(text):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text[:4000]
        }
    )


def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE) as f:
        return f.read()


def save_state(state):

    with open(STATE_FILE, "w") as f:
        f.write(state)

    os.system("git add state.txt")
    os.system("git commit -m update")
    os.system("git push")


address_id = get_address_id()

if not address_id:

    send("ПОМИЛКА: адресу не знайдено")
    exit()


schedule = get_schedule(address_id)

if not schedule:

    send("ПОМИЛКА: графік не отримано")
    exit()


new_hash = hashlib.md5(schedule.encode()).hexdigest()

old_hash = load_state()

if old_hash is None:

    send("✅ Бот запущено\nГрафік отримано")
    save_state(new_hash)

elif new_hash != old_hash:

    send("⚡ Графік змінено")
    save_state(new_hash)
