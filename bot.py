import asyncio
import hashlib
import os
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

from telethon import TelegramClient


# ========= CONFIG =========

api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

DTEK_BOT = "@DTEKKyivRegionElektromerezhiBot"

QUEUE = "1.2"

STATE_FILE = "state.txt"


# ========= TIME =========

def now():
    return datetime.now(ZoneInfo("Europe/Kyiv"))


# ========= STATE =========

def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    return open(STATE_FILE).read()


def save_state(s):
    open(STATE_FILE, "w").write(s)


# ========= FIND GRAPH =========

def find_graph_rows(arr):

    h, w = arr.shape

    rows = []

    for y in range(int(h*0.2), int(h*0.5)):

        line = arr[y]

        dark = np.sum(line < 160)

        if dark > w * 0.05:
            rows.append(y)

    if not rows:
        return None, None

    today = rows[0]

    tomorrow = None

    for y in rows:
        if y - today > 20:
            tomorrow = y
            break

    return today, tomorrow


# ========= READ DAY =========

def read_day(arr, y, left, right):

    w = right - left

    col_width = w / 24

    off = []

    for hour in range(24):

        x1 = int(left + hour * col_width)
        x2 = int(left + (hour+1) * col_width)

        mid = (x1 + x2) // 2

        left_block = arr[y-3:y+3, x1:mid]
        right_block = arr[y-3:y+3, mid:x2]

        if left_block.mean() < 170:
            off.append(hour*60)

        if right_block.mean() < 170:
            off.append(hour*60 + 30)

    return merge(off)


# ========= MERGE =========

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


# ========= READ GRAPH =========

def read_graph(path):

    img = Image.open(path).convert("L")

    arr = np.array(img)

    h, w = arr.shape

    left = int(w*0.15)
    right = int(w*0.95)

    today_y, tomorrow_y = find_graph_rows(arr)

    today = []
    tomorrow = []

    if today_y:
        today = read_day(arr, today_y, left, right)

    if tomorrow_y:
        tomorrow = read_day(arr, tomorrow_y, left, right)

    return today, tomorrow


# ========= CAPTION =========

def build_caption(path):

    today, tomorrow = read_graph(path)

    text = f"Черга {QUEUE}\n"
    text += f"Оновлено: {now().strftime('%d.%m.%Y %H:%M')}\n"

    if today:
        text += "\nСьогодні:\n"
        text += "\n".join(today)

    if tomorrow:
        text += "\n\nЗавтра:\n"
        text += "\n".join(tomorrow)

    return text


# ========= SEND =========

def send_photo(path):

    caption = build_caption(path)

    print(caption)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(path,"rb") as f:

        r = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": caption
            },
            files={"photo": f}
        )

    print(r.status_code, r.text)


# ========= GET GRAPH =========

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

    messages = await client.get_messages(bot, limit=5)

    for m in messages:
        if m.photo:
            path = "graph.jpg"
            await m.download_media(path)
            return path

    return None


# ========= MAIN =========

async def main():

    path = await get_graph()

    if not path:
        print("No graph")
        return

    new_hash = hashlib.md5(open(path,"rb").read()).hexdigest()

    old_hash = load_state()

    if new_hash != old_hash:

        send_photo(path)

        save_state(new_hash)

        print("Sent")

    else:

        print("No changes")


asyncio.run(main())
