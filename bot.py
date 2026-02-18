import requests
import hashlib
import os
from datetime import datetime

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

API_URL = "https://www.dtek-krem.com.ua/api/shutdowns"

GROUP = "1.2"

STATE_FILE = "state.txt"


def get_data():
    try:
        r = requests.get(API_URL, timeout=30)
        return r.json()
    except:
        return None


def parse_schedule(data):

    result = []
    now = datetime.now()
    power_off_now = False

    try:
        schedules = data.get("data", [])

        for day in schedules:

            date = day.get("date")

            for outage in day.get("shutdowns", []):

                if outage.get("group") == GROUP:

                    start_str = outage.get("start")
                    end_str = outage.get("end")

                    result.append(f"{date} {start_str}-{end_str}")

                    start = datetime.strptime(
                        f"{date} {start_str}",
                        "%Y-%m-%d %H:%M"
                    )

                    end = datetime.strptime(
                        f"{date} {end_str}",
                        "%Y-%m-%d %H:%M"
                    )

                    if start <= now <= end:
                        power_off_now = True

    except:
        pass

    return result, power_off_now


def send(text):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


def save_state(hash_value):

    with open(STATE_FILE, "w") as f:
        f.write(hash_value)

    os.system("git config user.name github-actions")
    os.system("git config user.email github-actions@github.com")

    os.system("git add state.txt")
    os.system("git commit -m update_state")
    os.system("git push")


def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as f:
        return f.read()


# main

data = get_data()

if not data:
    exit()

schedule, power_off = parse_schedule(data)

if not schedule:
    exit()

schedule_text = "\n".join(schedule)

status = "🔴 Зараз світла НЕМАЄ" if power_off else "🟢 Зараз світло Є"

full_text = status + "\n" + schedule_text

new_hash = hashlib.md5(full_text.encode()).hexdigest()

old_hash = load_state()

# перший запуск
if old_hash is None:

    message = (
        f"{status}\n\n"
        f"👥 Група {GROUP}\n\n"
        f"{schedule_text}\n\n"
        f"Перший запуск\n"
        f"{datetime.now().strftime('%H:%M')}"
    )

    send(message)
    save_state(new_hash)

# якщо змінилось
elif new_hash != old_hash:

    message = (
        f"{status}\n\n"
        f"👥 Група {GROUP}\n\n"
        f"{schedule_text}\n\n"
        f"Оновлено\n"
        f"{datetime.now().strftime('%H:%M')}"
    )

    send(message)
    save_state(new_hash)
