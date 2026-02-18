import requests
import hashlib
import os
from datetime import datetime

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

API_URL = "https://www.dtek-krem.com.ua/api/shutdowns"

GROUP = "1.2"


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

                    result.append(
                        f"{date}  {start_str} - {end_str}"
                    )

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


def get_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def send(text):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


data = get_data()

if not data:
    exit()

schedule, power_off = parse_schedule(data)

if not schedule:
    exit()

schedule_text = "\n".join(schedule)

if power_off:
    status = "🔴 Зараз світла НЕМАЄ"
else:
    status = "🟢 Зараз світло Є"

full_text = status + "\n\n" + schedule_text

new_hash = get_hash(full_text)

if os.path.exists("last.txt"):

    with open("last.txt", "r") as f:
        old_hash = f.read()

else:

    old_hash = ""


if new_hash != old_hash:

    message = (
        f"{status}\n\n"
        f"👥 Група: {GROUP}\n\n"
        f"📅 Графік:\n"
        f"{schedule_text}\n\n"
        f"Оновлено: {datetime.now().strftime('%H:%M')}"
    )

    send(message)

    with open("last.txt", "w") as f:
        f.write(new_hash)
