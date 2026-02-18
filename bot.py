import requests
import hashlib
import os

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

API_URL = "https://www.dtek-krem.com.ua/api/shutdowns"


payload = {
    "address": "Богуслав, Росьова 70"
}


def get_schedule():
    try:
        r = requests.post(API_URL, json=payload, timeout=30)
        return r.text
    except:
        return ""


def get_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


data = get_schedule()

if not data:
    exit()

new_hash = get_hash(data)

if os.path.exists("last_hash.txt"):
    with open("last_hash.txt", "r") as f:
        old_hash = f.read()
else:
    old_hash = ""

if new_hash != old_hash:

    send_message(
        "⚡ Оновлення графіка відключення\n"
        "📍 Богуслав, Росьова 70\n\n"
        "Перевірити:\n"
        "https://www.dtek-krem.com.ua/ua/shutdowns"
    )

    with open("last_hash.txt", "w") as f:
        f.write(new_hash)
