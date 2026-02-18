import requests
import hashlib
import os
from datetime import datetime

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

GROUP = "1.2"

STATE_FILE = "state.txt"

# реальний файл графіка (використовується frontend)
URL = "https://www.dtek-krem.com.ua/assets/json/schedule.json"


def get_json():

    try:

        r = requests.get(URL, timeout=30)

        print("Status:", r.status_code)

        return r.json()

    except Exception as e:

        print(e)
        return None


def parse(data):

    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M")

    result = []
    power_off = False

    try:

        for day in data:

            if day["date"] != today:
                continue

            groups = day["groups"]

            if GROUP not in groups:
                continue

            for period in groups[GROUP]:

                start = period["from"]
                end = period["to"]

                result.append(f"{start}-{end}")

                if start <= now <= end:
                    power_off = True

    except Exception as e:

        print(e)

    return result, power_off


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
    os.system("git commit -m state_update")
    os.system("git push")


# main

data = get_json()

if not data:

    send("ПОМИЛКА: не отримано JSON графіка")
    exit()

schedule, power_off = parse(data)

schedule_text = "\n".join(schedule) if schedule else "Немає відключень"

status = "🔴 Зараз світла НЕМАЄ" if power_off else "🟢 Зараз світло Є"

full = status + "\n" + schedule_text

new_hash = hashlib.md5(full.encode()).hexdigest()

old_hash = load_state()

if old_hash is None:

    send(
        f"✅ Бот запущено\n\n"
        f"{status}\n\n"
        f"Група {GROUP}\n\n"
        f"{schedule_text}"
    )

    save_state(new_hash)

elif new_hash != old_hash:

    send(
        f"⚡ Оновлення\n\n"
        f"{status}\n\n"
        f"Група {GROUP}\n\n"
        f"{schedule_text}"
    )

    save_state(new_hash)
