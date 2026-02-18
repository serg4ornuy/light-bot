import requests
import hashlib
import os
import re
from datetime import datetime

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

GROUP = "1.2"

STATE_FILE = "state.txt"

URL = "https://www.dtek-krem.com.ua/ua/shutdowns"


def get_page():

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(URL, headers=headers, timeout=30)

    return r.text


def extract_schedule(page):

    pattern = rf"{GROUP}.*?(\d{{2}}:\d{{2}}).*?(\d{{2}}:\d{{2}})"

    matches = re.findall(pattern, page)

    result = []

    power_off_now = False

    now = datetime.now().strftime("%H:%M")

    for start, end in matches:

        result.append(f"{start}-{end}")

        if start <= now <= end:

            power_off_now = True

    return result, power_off_now


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

    os.system("git add state.txt")
    os.system("git commit -m state_update")
    os.system("git push")


# main

page = get_page()

schedule, power_off = extract_schedule(page)

if not schedule:

    schedule_text = "Немає даних"
else:

    schedule_text = "\n".join(schedule)

status = "🔴 Зараз світла НЕМАЄ" if power_off else "🟢 Зараз світло Є"

full_text = status + "\n" + schedule_text

new_hash = hashlib.md5(full_text.encode()).hexdigest()

old_hash = load_state()


# перший запуск
if old_hash is None:

    message = (
        f"✅ Бот запущено\n\n"
        f"{status}\n\n"
        f"👥 Група {GROUP}\n\n"
        f"{schedule_text}\n\n"
        f"{datetime.now().strftime('%H:%M')}"
    )

    send(message)

    save_state(new_hash)


# якщо зміни
elif new_hash != old_hash:

    message = (
        f"⚡ Оновлення\n\n"
        f"{status}\n\n"
        f"👥 Група {GROUP}\n\n"
        f"{schedule_text}\n\n"
        f"{datetime.now().strftime('%H:%M')}"
    )

    send(message)

    save_state(new_hash)
