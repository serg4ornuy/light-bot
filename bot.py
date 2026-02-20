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


# CONFIG

api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

DTEK_BOT = "DTEKKyivRegionElektromerezhiBot"

QUEUE = "1.2"

STATE_FILE = "state.txt"


# TIME

def now_kyiv():
    return datetime.now(ZoneInfo("Europe/Kyiv"))


# FIND GRAPH AREA

def find_graph_area(arr):

    h, w = arr.shape

    y = int(h * 0.30)

    row = arr[y]

    dark = row < 180

    xs = np.where(dark)[0]

    if len(xs) == 0:
        return int(w*0.2), int(w*0.95)

    left = xs.min()
    right = xs.max()

    return left, right


# READ ONE ROW

def read_day(arr, y, left, right):

    width = right - left

    col_width = width / 24

    off_minutes = []

    for hour in range(24):

        x1 = int(left + hour * col_width)
        x2 = int(left + (hour + 1) * col_width)

        mid = (x1 + x2) // 2

        left_block = arr[y-5:y+5, x1:mid]
        right_block = arr[y-5:y+5, mid:x2]

        if left_block.mean() < 170:
            off_minutes.append(hour * 60)

        if right_block.mean() < 170:
            off_minutes.append(hour * 60 + 30)

    return merge_minutes(off_minutes)


# MERGE INTERVALS

def merge_minutes(minutes):

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

        sh = s//60
        sm = s%60

        eh = e//60
        em = e%60

        formatted.append(f"{sh:02}:{sm:02}–{eh:02}:{em:02}")

    return formatted


# READ SCHEDULE

def read_schedule(path):

    img = Image.open(path).convert("L")

    arr = np.array(img)

    left, right = find_graph_area(arr)

    h = arr.shape[0]

    today_y = int(h * 0.30)
    tomorrow_y = int(h * 0.38)

    rows = []

    today = read_day(arr, today_y, left, right)

    if today:
        rows.append(today)

    tomorrow = read_day(arr, tomorrow_y, left, right)

    if tomorrow:
        rows.append(tomorrow)

    return rows


# EXTRACT DATE

def extract_graph_date(text):

    match = re.search(r'(\d{2}\.\d{2}\.\d{4})', text)

    if match:
        return datetime.strptime(match.group(1), "%d.%m.%Y")

    return now_kyiv()


# BUILD CAPTION

def build_caption(path, graph_text):

    graph_date = extract_graph_date(graph_text)

    now = now_kyiv().strftime("%d.%m.%Y %H:%M")

    rows = read_schedule(path)

    caption = f"Черга {QUEUE}\nОновлено: {now}\n"

    if len(rows) >= 1:

        caption += f"\n{graph_date.strftime('%d.%m.%Y')}:\n"

        for i in rows[0]:
            caption += i + "\n"

    if len(rows) >= 2:

        caption += f"\n{(graph_date + timedelta(days=1)).strftime('%d.%m.%Y')}:\n"

        for i in rows[1]:
            caption += i + "\n"

    return caption


# SEND PHOTO

def send_photo(path, graph_text):

    caption = build_caption(path, graph_text)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(path, "rb") as f:

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": caption
            },
            files={"photo": f}
        )


# STATE

def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE).read()


def save_state(state):

    open(STATE_FILE, "w").write(state)


# GET GRAPH

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

    await asyncio.sleep(5)

    messages = await client.get_messages(bot, limit=5)

    for m in messages:

        if m.photo:

            path = "schedule.jpg"

            await m.download_media(path)

            return path, m.text or ""

    return None, ""


# MAIN

async def main():

    path, graph_text = await get_graph()

    if not path:
        return

    new_hash = hashlib.md5(graph_text.encode()).hexdigest()

    old_hash = load_state()

    if old_hash != new_hash:

        send_photo(path, graph_text)

        save_state(new_hash)


asyncio.run(main())
