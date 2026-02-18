import os
import hashlib
import time
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

CITY = "Богуслав"
STREET = "Росьова"
HOUSE = "70"

STATE_FILE = "state.txt"
IMAGE_FILE = "schedule.png"

URL = "https://www.dtek-krem.com.ua/ua/shutdowns"


def take_screenshot():

    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    driver.get(URL)

    time.sleep(5)

    inputs = driver.find_elements(By.TAG_NAME, "input")

    inputs[0].send_keys(CITY)
    time.sleep(1)

    inputs[1].send_keys(STREET)
    time.sleep(1)

    inputs[2].send_keys(HOUSE)
    time.sleep(1)

    inputs[2].send_keys(Keys.ENTER)

    time.sleep(5)

    driver.save_screenshot(IMAGE_FILE)

    driver.quit()


def get_hash():

    with open(IMAGE_FILE, "rb") as f:

        return hashlib.md5(f.read()).hexdigest()


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


def send_photo():

    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    with open(IMAGE_FILE, "rb") as photo:

        requests.post(
            url,
            data={"chat_id": CHAT_ID},
            files={"photo": photo}
        )


# main

take_screenshot()

new_hash = get_hash()

old_hash = load_state()

if old_hash is None:

    send_photo()

    save_state(new_hash)

elif new_hash != old_hash:

    send_photo()

    save_state(new_hash)
