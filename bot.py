import asyncio
import hashlib
import os
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

from telethon import TelegramClient


api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

DTEK_BOT = "@DTEKKyivRegionElektromerezhiBot"

QUEUE = "1.2"

STATE_FILE = "state.txt"


def now():
    return datetime.now(ZoneInfo("Europe/Kyiv"))


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    return open(STATE_FILE).read().strip()


def save_state(s):
    open(STATE_FILE, "w").write(s)


# ================= FIND GRID LINES =================

def find_vertical_lines(arr):

    h, w = arr.shape

    profile = np.sum(arr < 200, axis=0)

    lines = []

    in_line = False

    for x in range(w):

        if profile[x] > h * 0.05 and not in_line:

            start = x
            in_line = True

        elif profile[x] <= h * 0.05 and in_line:

            end = x

            lines.append((start + end)//2)

            in_line = False

    return lines


# ================= MERGE =================

def merge(minutes):

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

    return [
        f"{s//60:02}:{s%60:02}–{e//60:02}:{e%60:02}"
        for s,e in result
    ]


# ================= READ DAY =================

def read_day(arr, y, lines):

    off = []

    for hour in range(min(24, len(lines)-1)):

        left = lines[hour]
        right = lines[hour+1]

        mid = (left + right)//2

        left_block = arr[y-4:y+4, left:mid]
        right_block = arr[y-4:y+4, mid:right]

        if left_block.mean() < 160:
            off.append(hour * 60)

        if right_block.mean() < 160:
            off.append(hour * 60 + 30)

    return merge(off)


# ================= READ GRAPH =================

def read_graph(path):

    img = Image.open(path).convert("L")

    arr = np.array(img)

    lines = find_vertical_lines(arr)

    if len(lines) < 25:
        print("LINES FOUND:", len(lines))
        return [], []

    today_y = None
    tomorrow_y = None

    for y in range(arr.shape[0]):

        dark = np.sum(arr[y] < 150)

        if dark > arr.shape[1] * 0.05:

            if today_y is None:
                today_y = y

            elif tomorrow_y is None and abs(y - today_y) > 20:
                tomorrow_y = y
                break

    today = []
    tomorrow = []

    if today_y:
        today = read_day(arr, today_y, lines)

    if tomorrow_y:
        tomorrow = read_day(arr, tomorrow_y, lines)

    return today, tomorrow


# ================= BUILD TEXT =================

def build_caption(path):

    today, tomorrow = read_graph(path)

    text = f"Черга {QUEUE}\n"
    text += f"Оновлено: {now().strftime('%d.%m.%Y %H:%M')}\n"

    if today:
        text += "\nСьогодні:\n"
        text += "\n".join(today)

    if tomorrow:
        text += "\nЗавтра:\n"
        text += "\n".join(tomorrow)

    return text


# ================= SEND =================

def send_photo(path):

    caption = build_caption(path)

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


# ================= GET GRAPH =================

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

    messages = await client.get_messages(bot, limit=10)

    for m in messages:

        if m.photo:

            path = "graph.jpg"

            await m.download_media(path)

            return path

    return None


# ================= MAIN =================

async def main():

    path = await get_graph()

    if not path:
        return

    new_hash = hashlib.md5(open(path,"rb").read()).hexdigest()

    old_hash = load_state()

    if new_hash != old_hash:

        send_photo(path)

        save_state(new_hash)


asyncio.run(main())
