import requests
import hashlib
import os
import time

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

# використовуємо RSS новин DTEK як тригер
URL = "https://www.dtek-krem.com.ua/ua/shutdowns"


def get_page():

    try:

        r = requests.get(URL, timeout=30)

        return r.text

    except:

        return None


def send(text):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
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


data = get_page()

if not data:

    send("ПОМИЛКА: сайт недоступний")
    exit()


new_hash = hashlib.md5(data.encode()).hexdigest()

old_hash = load_state()

if old_hash is None:

    send("✅ Бот запущено і підключено до DTEK")
    save_state(new_hash)

elif new_hash != old_hash:

    send("⚡ DTEK оновив графік. Перевір:")
    send(URL)

    save_state(new_hash)
