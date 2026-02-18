import os
import hashlib
import time
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

CITY = "Богуслав"
STREET = "Росьова"
HOUSE = "70"

URL = "https://www.dtek-krem.com.ua/ua/shutdowns"


def get_data():

    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    driver.get(URL)

    time.sleep(5)

    # виконати JS як браузер
    result = driver.execute_script(f"""
        return fetch('/api/shutdowns/search', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify({{
                city: '{CITY}',
                street: '{STREET}',
                house: '{HOUSE}'
            }})
        }})
        .then(r => r.text())
    """)

    driver.quit()

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

    with open(STATE_FILE) as f:

        return f.read()


def save_state(state):

    with open(STATE_FILE, "w") as f:

        f.write(state)

    os.system("git add state.txt")
    os.system("git commit -m update")
    os.system("git push")


data = get_data()

if not data:

    data = "ПОМИЛКА: API не повернув дані"

new_hash = hashlib.md5(data.encode()).hexdigest()

old_hash = load_state()

if old_hash is None:

    send("✅ Бот запущено\n\n" + data)
    save_state(new_hash)

elif new_hash != old_hash:

    send("⚡ Оновлення\n\n" + data)
    save_state(new_hash)
