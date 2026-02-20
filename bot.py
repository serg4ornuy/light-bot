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


api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "ТВОЙ_BOT_TOKEN"
CHAT_ID = "-1003856095678"

DTEK_BOT = "DTEKKyivRegionElektromerezhiBot"

QUEUE = "1.2"

STATE_FILE = "state.txt"


def now_kyiv():
    return datetime.now(ZoneInfo("Europe/Kyiv"))


# ВИРІЗАЄ ВЕРХНЮ ТАБЛИЦЮ

def crop_main_graph(img):

    arr = np.array(img.convert("L"))

    h, w = arr.shape

    # шукаємо область де є "Черга"
    for y in range(int(h*0.05), int(h*0.3)):

        if arr[y].mean() < 240:

            top = y + 30
            break
    else:
        top = int(h*0.18)

    bottom = int(h*0.42)

    left = int(w*0.15)
    right = int(w*0.95)

    return arr[top:bottom, left:right]


def read_intervals(arr):

    h, w = arr.shape

    row_today = int(h*0.35)
    row_tomorrow = int(h*0.65)

    return [
        read_day(arr, row_today),
        read_day(arr, row_tomorrow)
    ]


def read_day(arr, y):

    h, w = arr.shape

    col_width = w / 24

    off = []

    for hour in range(24):

        x1 = int(hour * col_width)
        x2 = int((hour+1) * col_width)

        mid = (x1 + x2)//2

        left = arr[y-5:y+5, x1:mid]
        right = arr[y-5:y+5, mid:x2]

        if left.mean() < 180:
            off.append(hour*60)

        if right.mean() < 180:
            off.append(hour*60 + 30)

    return merge(off)


def merge(minutes):

    if not minutes:
        return []

    minutes = sorted(minutes)

    result = []

    start = minutes[0]
    prev = minutes[0]

    for m in minutes[1:]:

        if m == prev+30:
            prev = m
        else:
            result.append((start, prev+30))
            start = m
            prev = m

    result.append((start, prev+30))

    return [
        f"{s//60:02}:{s%60:02}–{e//60:02}:{e%60:02}"
        for s,e in result
    ]


def build_caption(path, text):

    img = Image.open(path)

    cropped = crop_main_graph(img)

    today, tomorrow = read_intervals(cropped)

    now = now_kyiv().strftime("%d.%m.%Y %H:%M")

    caption = f"Черга {QUEUE}\nОновлено: {now}\n"

    if today:
        caption += "\nСьогодні:\n"
        caption += "\n".join(today)

    if tomorrow:
        caption += "\n\nЗавтра:\n"
        caption += "\n".join(tomorrow)

    return caption


def send_photo(path, text):

    caption = build_caption(path, text)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(path,"rb") as f:

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": caption
            },
            files={"photo": f}
        )


def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE).read()


def save_state(state):

    open(STATE_FILE,"w").write(state)


async def get_graph():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    await client.send_message(bot, "/start")
    await asyncio.sleep(2)

    await client.send_message(bot, "Графік відключень🕒")
    await asyncio.sleep(3)

    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:
        await msg[0].click(text="Наступний >")

    await asyncio.sleep(2)

    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:
        await msg[0].click(text="✅ Обрати")

    await asyncio.sleep(4)

    messages = await client.get_messages(bot, limit=5)

    for m in messages:

        if m.photo:

            path = "graph.jpg"

            await m.download_media(path)

            return path, m.text or ""

    return None, ""


async def main():

    path, text = await get_graph()

    if not path:
        return

    new_hash = hashlib.md5(text.encode()).hexdigest()

    old_hash = load_state()

    if new_hash != old_hash:

        send_photo(path, text)

        save_state(new_hash)


asyncio.run(main())
