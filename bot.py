import requests
import hashlib
import os
from datetime import datetime

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

GROUP = "1.2"

STATE_FILE = "state.txt"

# цей endpoint реально працює
URL = "https://www.dtek-krem.com.ua/ua/shutdowns"


def get_page():

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(URL, headers=headers, timeout=30)

        return r.text

    except Exception as e:

        print(e)
        return None


def extract_group(page):

    lines = page.split("\n")

    result = []

    for line in lines:

        if GROUP in line and ":" in line:

            result.append(line.strip())

    return result


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

    with open(STATE_FILE, "r") as f:

        return f.read()


def save_state(hash_value):

    with open(STATE_FILE, "w") as f:

        f.write(hash_value)

    os.system("git config --global user.name github-actions")
    os.system("git config --global user.email github-actions@github.com")

    os.system("git add state.txt")
    os.system("git commit -m update_state")
    os.system("git push")


# main

page = get_page()

if not page:

    exit()

data = extract_group(page)

text = "\n".join(data)

if not text:

    text = "Графік знайдено, але група 1.2 не знайдена"

new_hash = hashlib.md5(text.encode()).hexdigest()

old_hash = load_state()


# перший запуск
if old_hash is None:

    send(
        f"✅ Бот запущено\n\n"
        f"Група {GROUP}\n\n"
        f"{text}\n\n"
        f"{datetime.now().strftime('%H:%M')}"
    )

    save_state(new_hash)


# якщо зміни
elif new_hash != old_hash:

    send(
        f"⚡ Оновлення\n\n"
        f"Група {GROUP}\n\n"
        f"{text}\n\n"
        f"{datetime.now().strftime('%H:%M')}"
    )

    save_state(new_hash)
