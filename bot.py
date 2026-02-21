import asyncio
import hashlib
import os
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient


# CONFIG

api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

DTEK_BOT = "DTEKKyivRegionElektromerezhiBot"

QUEUE = "Черга 1.2"


# GET SCHEDULE IMAGE

async def get_schedule():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    print("START")

    # start
    await client.send_message(bot, "/start")
    await asyncio.sleep(3)

    # menu
    await client.send_message(bot, "Графік відключень🕒")
    await asyncio.sleep(3)

    # next
    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:
        print("CLICK NEXT")
        await msg[0].click(text="Наступний >")

    await asyncio.sleep(3)

    # select
    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:
        print("CLICK SELECT")
        await msg[0].click(text="✅ Обрати")

    await asyncio.sleep(5)

    # find photo
    messages = await client.get_messages(bot, limit=5)

    file_path = None

    for m in messages:

        if m.photo:

            file_path = "schedule.jpg"

            await m.download_media(file_path)

            print("PHOTO DOWNLOADED")

            break

    await client.disconnect()

    return file_path


# SEND PHOTO WITH TEXT

def send_photo(path):

    now = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%d.%m.%Y %H:%M")

    caption = f"{QUEUE}\nОновлено: {now}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(path, "rb") as f:

        r = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": caption
            },
            files={"photo": f}
        )

    print("TELEGRAM STATUS:", r.status_code)
    print(r.text)


# STATE

def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE).read()


def save_state(state):

    open(STATE_FILE, "w").write(state)


# MAIN

async def main():

    path = await get_schedule()

    if not path:
        print("Фото не знайдено")
        return

    data = open(path, "rb").read()

    new_hash = hashlib.md5(data).hexdigest()

    old_hash = load_state()

    print("HASH:", new_hash)

    if old_hash is None:

        print("FIRST SEND")

        send_photo(path)

        save_state(new_hash)

    elif new_hash != old_hash:

        print("GRAPH CHANGED")

        send_photo(path)

        save_state(new_hash)

    else:

        print("NO CHANGE")


asyncio.run(main())
