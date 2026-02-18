import asyncio
import hashlib
import os
import requests

from playwright.async_api import async_playwright

TOKEN = "ТВОЙ_TOKEN"
CHAT_ID = "ТВОЙ_CHAT_ID"

STATE_FILE = "state.txt"

URL = "https://www.dtek-krem.com.ua/ua/shutdowns"


async def get_schedule():

    async with async_playwright() as p:

        browser = await p.chromium.launch()

        page = await browser.new_page()

        await page.goto(URL)

        # чекати popup і закрити
        try:
            await page.click("button:has-text('×')", timeout=5000)
        except:
            pass

        await page.wait_for_selector("table")

        content = await page.locator("table").inner_text()

        await browser.close()

        return content


def send(text):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text}
    )


def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE).read()


def save_state(state):

    open(STATE_FILE, "w").write(state)


schedule = asyncio.run(get_schedule())

new_hash = hashlib.md5(schedule.encode()).hexdigest()

old_hash = load_state()

if old_hash is None:

    send("Бот запущено\n\n" + schedule)

    save_state(new_hash)

elif new_hash != old_hash:

    send("Графік змінено\n\n" + schedule)

    save_state(new_hash)
