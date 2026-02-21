import asyncio
import hashlib
import os
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient


# ================= CONFIG =================

api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

DTEK_BOT = "DTEKKyivRegionElektromerezhiBot"

QUEUE = "Черга 1.2"


# ================= GET IMAGE =================

async def get_schedule():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    print("START")

    await client.send_message(bot, "/start")
    await asyncio.sleep(3)

    await client.send_message(bot, "Графік відключень🕒")
    await asyncio.sleep(3)

    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:

        print("CLICK NEXT")

        await msg[0].click(text="Наступний >")

    await asyncio.sleep(3)

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


# ================= TELEGRAM SEND =================

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


# ================= STATE =================

def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE).read().strip()


def save_state(state):

    with open(STATE_FILE, "w") as f:
        f.write(state)


def git_push():

    os.system('git config --global user.name "github-actions"')
    os.system('git config --global user.email "actions@github.com"')

    os.system("git add state.txt")

    os.system('git commit -m "update state" || exit 0')

    os.system("git push")


# ================= MAIN =================

async def main():

    path = await get_schedule()

    if not path:

        print("PHOTO NOT FOUND")

        return

    data = open(path, "rb").read()

    new_hash = hashlib.md5(data).hexdigest()

    old_hash = load_state()

    print("NEW HASH:", new_hash)
    print("OLD HASH:", old_hash)

    if old_hash is None:

        print("FIRST RUN → SEND")

        send_photo(path)

        save_state(new_hash)

        git_push()

    elif new_hash != old_hash:

        print("GRAPH CHANGED → SEND")

        send_photo(path)

        save_state(new_hash)

        git_push()

    else:

        print("NO CHANGE")


# ================= RUN =================

asyncio.run(main())
