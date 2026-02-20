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


# ================= CROP COPY =================

def crop_graph(original):

    img = Image.open(original)

    cropped = img.crop((0, 0, 1014, 411))

    path = "graph_crop.jpg"

    cropped.save(path)

    return path


# ================= FIND LAST LINE =================

def find_last_vertical_line(arr):

    h, w = arr.shape

    profile = np.sum((arr > 180) & (arr < 240), axis=0)

    xs = np.where(profile > h * 0.3)[0]

    return xs[-1]


# ================= FIND DAY ROW =================

def find_day_row(arr):

    h, w = arr.shape

    for y in range(int(h*0.3), int(h*0.7)):

        if np.sum(arr[y] < 140) > w * 0.05:
            return y

    return None


# ================= MERGE =================

def merge(minutes):

    if not minutes:
        return []

    minutes = sorted(set(minutes))

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

def read_day(arr, y, last_line):

    cell_width = 30  # стабільна ширина клітинки після crop

    first_line = last_line - (24 * cell_width)

    off = []

    for hour in range(24):

        x1 = int(first_line + hour * cell_width)
        x2 = int(x1 + cell_width)

        mid = (x1 + x2) // 2

        lx = (x1 + mid) // 2
        rx = (mid + x2) // 2

        if arr[y, lx] < 160:
            off.append(hour * 60)

        if arr[y, rx] < 160:
            off.append(hour * 60 + 30)

    return merge(off)


# ================= READ GRAPH =================

def read_graph(original):

    crop = crop_graph(original)

    img = Image.open(crop).convert("L")

    arr = np.array(img)

    last_line = find_last_vertical_line(arr)

    today_y = find_day_row(arr)

    tomorrow_y = today_y + 60

    today = read_day(arr, today_y, last_line)
    tomorrow = read_day(arr, tomorrow_y, last_line)

    return today, tomorrow


# ================= BUILD TEXT =================

def build_caption(original):

    today, tomorrow = read_graph(original)

    text = f"Черга {QUEUE}\n"
    text += f"Оновлено: {now().strftime('%d.%m.%Y %H:%M')}\n"

    if today:
        text += "\nСьогодні:\n"
        text += "\n".join(today)

    if tomorrow:
        text += "\nЗавтра:\n"
        text += "\n".join(tomorrow)

    return text


# ================= SEND ORIGINAL =================

def send_photo(original):

    caption = build_caption(original)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(original, "rb") as f:

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
