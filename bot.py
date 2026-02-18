import requests
import hashlib
import os
from datetime import datetime

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

GROUP = "1.2"

STATE_FILE = "state.txt"

# реальний JSON файл графіка (стабільний)
JSON_URL = "https://www.dtek-krem.com.ua/uploads/schedule/schedule.json"


def get_schedule():

    try:

        r = requests.get(JSON_URL, timeout=30)

        return r.json()

    except Exception as e:

        print(e)
        return None


def extract_group(data):

    now = datetime.now().strftime("%H:%M")

    result = []

    power_off = False

    today = datetime.now().strftime("%Y-%m-%d")

    try:

        days = data.get("days", [])

        for day in days:

            if day.get("date") != today:
                continue

            groups = day.get("groups", {})

            if GROUP not in groups:
                continue

            periods = groups[GROUP]

            for period in periods:

                start = period["start"]
                end = period["end"]

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

    with open(STATE_FILE, "r") as f:

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

    exit()

schedule, power_off = extract_group(data)

schedule_text = "\n".join(schedule) if schedule else "Немає відключень"

status = "🔴 Зараз світла НЕМАЄ" if power_off else "🟢 Зараз світло Є"

full = status + "\n" + schedule_text

new_hash = hashlib.md5(full.encode()).hexdigest()

old_hash = load_state()


# перший запуск
if old_hash is None:

    send(
        f"✅ Бот запущено\n\n"
        f"{status}\n\n"
        f"👥 Група {GROUP}\n\n"
        f"{schedule_text}"
    )

    save_state(new_hash)


# зміни
elif new_hash != old_hash:

    send(
        f"⚡ Оновлення\n\n"
        f"{status}\n\n"
        f"👥 Група {GROUP}\n\n"
        f"{schedule_text}"
    )

    save_state(new_hash)
