import hashlib
import os
from datetime import datetime
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

GROUP = "1.2"

STATE_FILE = "state.txt"

URL = "https://www.dtek-krem.com.ua/ua/shutdowns"


def get_schedule():

    options = Options()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    driver.get(URL)

    time.sleep(5)

    body = driver.find_element(By.TAG_NAME, "body").text

    driver.quit()

    lines = body.split("\n")

    result = []

    now = datetime.now().strftime("%H:%M")

    power_off = False

    for line in lines:

        if GROUP in line and "-" in line:

            result.append(line)

            parts = line.split()

            for part in parts:

                if "-" in part:

                    start, end = part.split("-")

                    if start <= now <= end:

                        power_off = True

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
    os.system("git commit -m update")
    os.system("git push")


schedule, power_off = get_schedule()

text = "\n".join(schedule)

status = "🔴 Зараз світла НЕМАЄ" if power_off else "🟢 Зараз світло Є"

full = status + text

new_hash = hashlib.md5(full.encode()).hexdigest()

old_hash = load_state()

if old_hash is None:

    send(
        f"✅ Бот запущено\n\n"
        f"{status}\n\n"
        f"{text}"
    )

    save_state(new_hash)

elif new_hash != old_hash:

    send(
        f"⚡ Оновлення\n\n"
        f"{status}\n\n"
        f"{text}"
    )

    save_state(new_hash)
