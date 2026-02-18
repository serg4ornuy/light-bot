import requests
import hashlib
import os

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

URLS = [
    "https://www.dtek-krem.com.ua/assets/data/shutdowns/week.json",
    "https://www.dtek-krem.com.ua/assets/json/shutdowns.json"
]


def get_json():

    for url in URLS:

        try:

            r = requests.get(url, timeout=30)

            if r.status_code == 200 and len(r.text) > 100:

                return r.text

        except:
            pass

    return None


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


data = get_json()

if not data:

    send("ПОМИЛКА: не вдалося отримати графік")
    exit()


new_hash = hashlib.md5(data.encode()).hexdigest()

old_hash = load_state()

if old_hash is None:

    send("✅ Бот запущено\nГрафік отримано")
    save_state(new_hash)

elif new_hash != old_hash:

    send("⚡ Графік оновлено")
    save_state(new_hash)
