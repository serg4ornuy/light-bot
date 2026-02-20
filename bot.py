import asyncio
import hashlib
import os
import requests
import re

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

from telethon import TelegramClient


# ================= CONFIG =================

api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

DTEK_BOT = "@DTEKKyivRegionElektromerezhiBot"

QUEUE = "1.2"

STATE_FILE = "state.txt"


# ================= TIME =================

def now():
    return datetime.now(ZoneInfo("Europe/Kyiv"))


# ================= STATE =================

def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    return open(STATE_FILE).read().strip()


def save_state(s):
    open(STATE_FILE, "w").write(s)


# ================= GRAPH READER =================

def crop_graph(image):

    img = image.convert("L")
    arr = np.array(img)

    h, w = arr.shape

    # верхня таблиця знаходиться приблизно тут
    top = int(h * 0.18)
    bottom = int(h * 0.42)

    left = int(w * 0.15)
    right = int(w * 0.95)

    return arr[top:bottom, left:right]


def read_day(arr, y):

    h, w = arr.shape

    col_width = w / 24

    off = []

    for hour in range(24):

        x1 = int(hour * col_width)
        x2 = int((hour + 1) * col_width)

        mid = (x1 + x2) // 2

        left_block = arr[y-4:y+4, x1:mid]
        right_block = arr[y-4:y+4, mid:x2]

        if left_block.mean() < 170:
            off.append(hour * 60)

        if right_block.mean() < 170:
            off.append(hour * 60 + 30)

    return merge_intervals(off)


def merge_intervals(minutes):

    if not minutes:
        return []

    minutes = sorted(minutes)

    result = []

    start = minutes[0]
    prev = minutes[0]

    for m in minutes[1:]:

        if m == prev + 30:
            prev = m
        else:
            result.append((start, prev+30))
            start = m
            prev = m

    result.append((start, prev+30))

    formatted = []

    for s, e in result:

        formatted.append(
            f"{s//60:02}:{s%60:02}–{e//60:02}:{e%60:02}"
        )

    return formatted


def read_graph(path):

    img = Image.open(path)

    arr = crop_graph(img)

    h, w = arr.shape

    today_y = int(h * 0.35)
    tomorrow_y = int(h * 0.65)

    today = read_day(arr, today_y)
    tomorrow = read_day(arr, tomorrow_y)

    return today, tomorrow


# ================= TELEGRAM SEND =================

def send_photo(path, caption):

    print("SEND PHOTO")

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

    print("STATUS:", r.status_code)
    print(r.text)


# ================= CAPTION =================

def build_caption(path):

    today, tomorrow = read_graph(path)

    now_str = now().strftime("%d.%m.%Y %H:%M")

    text = f"Черга {QUEUE}\n"
    text += f"Оновлено: {now_str}\n"

    if today:
        text += "\nСьогодні:\n"
        for i in today:
            text += i + "\n"

    if tomorrow:
        text += "\nЗавтра:\n"
        for i in tomorrow:
            text += i + "\n"

    return text


# ================= GET GRAPH FROM DTEK =================

async def get_graph():

    print("CONNECT TELEGRAM")

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    print("SEND /start")
    await client.send_message(bot, "/start")

    await asyncio.sleep(2)

    print("SEND menu")
    await client.send_message(bot, "Графік відключень🕒")

    await asyncio.sleep(3)

    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:

        print("CLICK Next")

        try:
            await msg[0].click(text="Наступний >")
        except:
            pass

    await asyncio.sleep(2)

    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:

        print("CLICK Обрати")

        try:
            await msg[0].click(text="✅ Обрати")
        except:
            pass

    await asyncio.sleep(5)

    messages = await client.get_messages(bot, limit=5)

    for m in messages:

        if m.photo:

            path = "graph.jpg"

            await m.download_media(path)

            print("PHOTO SAVED")

            return path

    print("PHOTO NOT FOUND")

    return None


# ================= MAIN =================

async def main():

    print("START")

    path = await get_graph()

    if not path:
        print("NO GRAPH")
        return

    caption = build_caption(path)

    print("CAPTION:")
    print(caption)

    new_hash = hashlib.md5(open(path,"rb").read()).hexdigest()

    old_hash = load_state()

    if new_hash != old_hash:

        send_photo(path, caption)

        save_state(new_hash)

        print("SENT")

    else:

        print("NO CHANGES")


# ================= RUN =================

asyncio.run(main())
