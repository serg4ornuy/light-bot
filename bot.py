import asyncio
import os
import hashlib
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

import cv2
import numpy as np

from telethon import TelegramClient


# CONFIG

API_ID = 37132117
API_HASH = "03e024f62a62ecd99bda067e6a2d1824"

DTEK_BOT = "@DTEKKyivRegionElektromerezhiBot"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHANNEL_ID = -1003856095678

GRAPH_FILE = "graph.jpg"
STATE_FILE = "state.txt"

QUEUE = "Черга 1.2"


# STATE

def get_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_state():
    if not os.path.exists(STATE_FILE):
        return ""
    return open(STATE_FILE).read().strip()


def save_state(h):
    open(STATE_FILE, "w").write(h)


# TELEGRAM SEND

def send(text):

    print("SENDING...")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(GRAPH_FILE, "rb") as f:

        r = requests.post(
            url,
            data={
                "chat_id": CHANNEL_ID,
                "caption": text
            },
            files={"photo": f}
        )

    print("STATUS:", r.status_code)
    print(r.text)


# DTEK GRAPH

async def get_graph():

    async with TelegramClient("session", API_ID, API_HASH) as client:

        bot = await client.get_entity(DTEK_BOT)

        print("OPEN MENU")

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

            await msg[0].click(text="Обрати")

        await asyncio.sleep(5)

        msgs = await client.get_messages(bot, limit=10)

        for m in msgs:

            if m.photo:

                await m.download_media(GRAPH_FILE)

                print("GRAPH SAVED")

                return True

    return False


# MAIN

async def main():

    print("START")

    ok = await get_graph()

    if not ok:

        print("FAILED TO GET GRAPH")

        return

    h = get_hash(GRAPH_FILE)

    old = load_state()

    print("HASH:", h)

    if h == old:

        print("NO CHANGE")

        return

    save_state(h)

    now = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%d.%m.%Y %H:%M")

    text = f"{QUEUE}\nОновлено: {now}"

    send(text)

    print("DONE")


asyncio.run(main())
