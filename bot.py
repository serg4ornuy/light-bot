import os
import hashlib
import time
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    wait = WebDriverWait(driver, 20)

    driver.get(URL)

    time.sleep(3)

    # Закрити popup якщо є
    try:

        close_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button"))
        )

        close_button.click()

        time.sleep(2)

    except:
        pass

    # знайти input поля
    inputs = wait.until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
    )

    # ввод адреси через JS (надійніше)
    driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[2].value = arguments[3];
        arguments[4].value = arguments[5];
    """,
        inputs[0], CITY,
        inputs[1], STREET,
        inputs[2], HOUSE
    )

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
