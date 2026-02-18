import requests
import hashlib
import os

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

URL = "https://www.dtek-krem.com.ua/ua/shutdowns"


def get_page():
    try:
        r = requests.get(URL, timeout=30)
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


page = get_page()

if not page:
    exit()

new_hash = get_hash(page)

if os.path.exists("last_hash.txt"):
    with open("last_hash.txt", "r") as f:
        old_hash = f.read()
else:
    old_hash = ""

if new_hash != old_hash:
    send_message("⚡ Графік відключень оновлено\nhttps://www.dtek-krem.com.ua/ua/shutdowns")

    with open("last_hash.txt", "w") as f:
        f.write(new_hash)
