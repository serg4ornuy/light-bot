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

    match = re.search(r'(\d{2}\.\d{2}\.\d{4})', text)

    if match:
        return datetime.strptime(match.group(1), "%d.%m.%Y")

    return now_kyiv()


# READ ROW

def read_row(arr, y, width):

    row = arr[y]

    threshold = 110

    dark = row < threshold

    segments = []

    start = None

    for i, val in enumerate(dark):

        if val and start is None:
            start = i

        elif not val and start is not None:
            segments.append((start, i))
            start = None

    if start is not None:
        segments.append((start, len(dark)))

    result = []

    for s, e in segments:

        start_hour = (s / width) * 24
        end_hour = (e / width) * 24

        sh = int(start_hour)
        sm = int((start_hour % 1) * 60)

        eh = int(end_hour)
        em = int((end_hour % 1) * 60)

        result.append(f"{sh:02}:{sm:02}–{eh:02}:{em:02}")

    return result


# AUTO-DETECT ROWS

def read_schedule(path):

    img = Image.open(path).convert("L")

    arr = np.array(img)

    h, w = arr.shape

    # перевіряємо кілька можливих позицій
    possible_rows = [
        int(h * 0.55),
        int(h * 0.68)
    ]

    results = []

    for y in possible_rows:

        row = read_row(arr, y, w)

        if row:
            results.append(row)

    return results


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

        for t in rows[0]:
            caption += t + "\n"

    elif len(rows) >= 2:

        date1 = graph_date.strftime("%d.%m.%Y")
        date2 = (graph_date + timedelta(days=1)).strftime("%d.%m.%Y")

        caption += f"\n{date1}:\n"

        for t in rows[0]:
            caption += t + "\n"

        caption += f"\n{date2}:\n"

        for t in rows[1]:
            caption += t + "\n"

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
