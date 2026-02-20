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


# ===== MERGE =====

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


# ===== FIND DAY ROW =====

def find_day_row(arr):

    h, w = arr.shape

    for y in range(int(h*0.2), int(h*0.5)):

        dark = np.sum(arr[y] < 140)

        if dark > w * 0.03:
            return y

    return None


# ===== FIND BLOCKS =====

def find_blocks(arr, y):

    h, w = arr.shape

    blocks = []

    in_block = False

    for x in range(w):

        col = arr[y-3:y+3, x]

        if col.mean() < 160:

            if not in_block:
                start = x
                in_block = True

        else:

            if in_block:
                end = x
                center = (start + end)//2
                blocks.append(center)
                in_block = False

    return blocks


# ===== CONVERT BLOCKS TO TIME =====

def blocks_to_time(blocks, width):

    minutes = []

    cell = width / 24

    for x in blocks:

        hour = int(x / cell)

        offset = (x % cell)

        if offset < cell/2:
            minutes.append(hour*60)
        else:
            minutes.append(hour*60+30)

    return merge(minutes)


# ===== READ GRAPH =====

def read_graph(path):

    img = Image.open(path).convert("L")

    arr = np.array(img)

    h, w = arr.shape

    today_y = find_day_row(arr)

    tomorrow_y = today_y + int(h*0.07)

    today_blocks = find_blocks(arr, today_y)
    tomorrow_blocks = find_blocks(arr, tomorrow_y)

    today = blocks_to_time(today_blocks, w)
    tomorrow = blocks_to_time(tomorrow_blocks, w)

    return today, tomorrow


# ===== BUILD TEXT =====

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


# ===== SEND =====

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


# ===== GET GRAPH =====

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


# ===== MAIN =====

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
