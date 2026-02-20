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


# EXTRACT GRAPH DATE

def extract_graph_date(text):

    match = re.search(r'(\d{2}\.\d{2}\.\d{2024})', text)

    if match:
        return datetime.strptime(match.group(1), "%d.%m.%Y")

    return now_kyiv()


# READ BLOCKS (48 blocks of 30 min)

def read_row_blocks(arr, y, width):

    blocks = 48

    block_width = width / blocks

    result = []

    state = False
    start_block = None

    for i in range(blocks):

        x1 = int(i * block_width)
        x2 = int((i + 1) * block_width)

        segment = arr[y, x1:x2]

        avg = segment.mean()

        is_dark = avg < 140

        if is_dark and not state:

            start_block = i
            state = True

        elif not is_dark and state:

            result.append((start_block, i))
            state = False

    if state:
        result.append((start_block, blocks))

    intervals = []

    for start, end in result:

        start_minutes = start * 30
        end_minutes = end * 30

        sh = start_minutes // 60
        sm = start_minutes % 60

        eh = end_minutes // 60
        em = end_minutes % 60

        intervals.append(f"{sh:02}:{sm:02}–{eh:02}:{em:02}")

    return intervals


# READ SCHEDULE

def read_schedule(path):

    img = Image.open(path).convert("L")

    arr = np.array(img)

    h, w = arr.shape

    positions = [
        int(h * 0.55),
        int(h * 0.68)
    ]

    rows = []

    for y in positions:

        intervals = read_row_blocks(arr, y, w)

        if intervals:
            rows.append(intervals)

    return rows


# CAPTION

def build_caption(path, graph_text):

    graph_date = extract_graph_date(graph_text)

    now = now_kyiv().strftime("%d.%m.%Y %H:%M")

    rows = read_schedule(path)

    caption = (
        f"Черга {QUEUE}\n"
        f"Оновлено: {now}\n"
    )

    if len(rows) == 1:

        date = graph_date.strftime("%d.%m.%Y")

        caption += f"\n{date}:\n"

        for i in rows[0]:
            caption += i + "\n"

    elif len(rows) >= 2:

        date1 = graph_date.strftime("%d.%m.%Y")
        date2 = (graph_date + timedelta(days=1)).strftime("%d.%m.%Y")

        caption += f"\n{date1}:\n"

        for i in rows[0]:
            caption += i + "\n"

        caption += f"\n{date2}:\n"

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

    file_path = None
    graph_text = ""

    for m in messages:

        if m.photo:

            file_path = "schedule.jpg"

            await m.download_media(file_path)

            graph_text = m.text or ""

            break

    await client.disconnect()

    return file_path, graph_text


# MAIN

async def main():

    path, graph_text = await get_graph()

    if not path:
        return

    new_hash = hashlib.md5(graph_text.encode()).hexdigest()

    old_hash = load_state()

    if old_hash is None:

        send_photo(path, graph_text)

        save_state(new_hash)

    elif new_hash != old_hash:

        send_photo(path, graph_text)

        save_state(new_hash)


asyncio.run(main())
