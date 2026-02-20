import asyncio
import hashlib
import os
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageEnhance

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


# ================= CROP =================

def crop_graph(original):

    img = Image.open(original)

    cropped = img.crop((0, 0, 1014, 411))

    path = "graph_crop.png"

    cropped.save(path)

    return path


# ================= MONOCHROME =================

def to_monochrome(path):

    img = Image.open(path).convert("L")

    enhancer = ImageEnhance.Contrast(img)

    img = enhancer.enhance(2.0)

    arr = np.array(img)

    mono = np.where(arr < 160, 0, 255).astype(np.uint8)

    Image.fromarray(mono).save("graph_mono.png")

    return mono


# ================= FIND LAST LINE =================

def find_last_vertical_line(arr):

    h, w = arr.shape

    profile = np.sum(arr == 0, axis=0)

    xs = np.where(profile > h * 0.2)[0]

    if len(xs) == 0:
        return None

    return xs[-1]


# ================= FIND TODAY ROW =================

def find_today_row(arr):

    h, w = arr.shape

    for y in range(int(h*0.25), int(h*0.7)):

        if np.sum(arr[y] == 0) > w * 0.05:
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

    cell = 30

    first_line = last_line - cell * 24

    minutes = []

    for hour in range(24):

        x1 = int(first_line + hour * cell)
        x2 = int(x1 + cell)

        if x1 < 0 or x2 >= arr.shape[1]:
            continue

        mid = (x1 + x2) // 2

        left_block = arr[y-4:y+4, x1:mid]
        right_block = arr[y-4:y+4, mid:x2]

        if np.mean(left_block) < 128:
            minutes.append(hour*60)

        if np.mean(right_block) < 128:
            minutes.append(hour*60+30)

    return merge(minutes)


# ================= READ GRAPH =================

def read_graph(original):

    crop = crop_graph(original)

    mono = to_monochrome(crop)

    last_line = find_last_vertical_line(mono)

    if last_line is None:
        return [], []

    today_y = find_today_row(mono)

    if today_y is None:
        return [], []

    today = read_day(mono, today_y, last_line)

    tomorrow_y = today_y + 60

    tomorrow = []

    if tomorrow_y < mono.shape[0]:

        if np.sum(mono[tomorrow_y] == 0) > mono.shape[1] * 0.05:

            tomorrow = read_day(mono, tomorrow_y, last_line)

    return today, tomorrow


# ================= BUILD TEXT =================

def build_caption(original):

    today, tomorrow = read_graph(original)

    text = f"Черга {QUEUE}\n"
    text += f"Оновлено: {now().strftime('%d.%m.%Y %H:%M')}\n"

    if today:

        text += "\nСьогодні:\n"

        for t in today:
            text += t + "\n"

    if tomorrow:

        text += "\nЗавтра:\n"

        for t in tomorrow:
            text += t + "\n"

    return text


# ================= SEND PHOTO =================

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
