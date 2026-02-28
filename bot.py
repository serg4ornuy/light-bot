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


# STATE

def load_state():

    if not os.path.exists(STATE_FILE):

        print("STATE FILE NOT FOUND")

        return None

    with open(STATE_FILE, "r") as f:

        data = f.read().strip()

        print("STATE LOADED:", data)

        return data


def save_state(state):

    print("SAVING STATE:", state)

    with open(STATE_FILE, "w") as f:

        f.write(state)


def git_push():

    print("PUSH STATE TO GITHUB")

    os.system('git config --global user.name "github-actions"')
    os.system('git config --global user.email "actions@github.com"')

    os.system("git add state.txt")

    os.system('git commit -m "update state" || exit 0')

    os.system("git push")


# GET IMAGE

async def get_schedule():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    print("OPEN BOT")

    await client.send_message(bot, "Меню")
    await asyncio.sleep(3)

    await client.send_message(bot, "Графік відключень🕒")
    await asyncio.sleep(3)

    # одразу шукаємо кнопку Обрати
    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:

        print("CLICK SELECT")

        await msg[0].click(text="✅ Обрати")

    await asyncio.sleep(5)

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


# SEND PHOTO

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


# MAIN

async def main():

    path = await get_schedule()

    if not path:

        print("NO PHOTO")

        return

    data = open(path, "rb").read()

    new_hash = hashlib.md5(data).hexdigest()

    print("NEW HASH:", new_hash)

    old_hash = load_state()

    if old_hash is None:

        print("FIRST RUN")

        send_photo(path)

        save_state(new_hash)

        git_push()

    elif new_hash != old_hash:

        print("GRAPH CHANGED")

        send_photo(path)

        save_state(new_hash)

        git_push()

    else:

        print("NO CHANGE")


asyncio.run(main())
