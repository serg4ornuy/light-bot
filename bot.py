import requests
import hashlib
import os
from datetime import datetime

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

GROUP = "1.2"

STATE_FILE = "state.txt"

API_URL = "https://www.dtek-krem.com.ua/api/shutdowns/by-group"


def get_schedule():

    try:

        r = requests.post(
            API_URL,
            json={"group": GROUP},
            timeout=30
        )

        print(r.text)

        return r.json()

    except Exception as e:

        print(e)
        return None


def parse(data):

    now = datetime.now()
    now_str = now.strftime("%H:%M")

    result = []

    power_off = False

    try:

        for item in data["data"]:

            date = item["date"]

            for period in item["periods"]:

                start = period["start"]
                end = period["end"]

                result.append(f"{date} {start}-{end}")

                if start <= now_str <= end:

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

data = get_schedule()

if not data:

    send("ПОМИЛКА: API не повернув дані")
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
