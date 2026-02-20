import asyncio
import hashlib
import os
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

from telethon import TelegramClient


# CONFIG

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


# ================= FIND COLUMNS =================

def find_columns(arr):

    h, w = arr.shape

    # беремо горизонтальний зріз таблиці
    y = int(h * 0.35)

    row = arr[y]

    # світлі лінії таблиці
    mask = row > 200

    edges = []

    in_line = False

    for x in range(w):

        if mask[x] and not in_line:

            start = x
            in_line = True

        elif not mask[x] and in_line:

            end = x

            if end - start > 2:

                edges.append((start + end)//2)

            in_line = False

    columns = []

    for i in range(len(edges)-1):

        left = edges[i]
        right = edges[i+1]

        if right - left > 5:

            columns.append((left, right))

    # беремо тільки 24
    if len(columns) >= 24:

        columns = columns[:24]

    return columns


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

def read_day(arr, y, columns):

    off = []

    for hour, (left, right) in enumerate(columns):

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

    columns = find_columns(arr)

    if len(columns) < 24:

        print("COLUMNS NOT FOUND:", len(columns))

        return [], []

    # знайти рядки
    today_y = None
    tomorrow_y = None

    for y in range(arr.shape[0]):

        dark = np.sum(arr[y, columns[0][0]:columns[-1][1]] < 150)

        if dark > 50:

            if today_y is None:

                today_y = y

            elif tomorrow_y is None and abs(y - today_y) > 20:

                tomorrow_y = y

                break

    today = []
    tomorrow = []

    if today_y:
        today = read_day(arr, today_y, columns)

    if tomorrow_y:
        tomorrow = read_day(arr, tomorrow_y, columns)

    print("TODAY:", today)
    print("TOMORROW:", tomorrow)

    return today, tomorrow


# ================= BUILD CAPTION =================

def build_caption(path):

    today, tomorrow = read_graph(path)

    text = f"Черга {QUEUE}\n"
    text += f"Оновлено: {now().strftime('%d.%m.%Y %H:%M')}\n"

    if today:

        text += "\nСьогодні:\n"

        for i in today:
            text += i + "\n"

    if tomorrow:

        text += "\nЗавтра:\n"

        for i in tomorrow:
            text += i + "\n"

    return text


# ================= SEND =================

def send_photo(path):

    caption = build_caption(path)

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
        try:
            await msg[0].click(text="Наступний >")
        except:
            pass

    await asyncio.sleep(2)

    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:
        try:
            await msg[0].click(text="✅ Обрати")
        except:
            pass

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
