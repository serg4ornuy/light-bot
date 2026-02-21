import asyncio
import os
import hashlib
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

import cv2
import numpy as np

from telethon import TelegramClient


# ================= CONFIG =================

API_ID = 37132117
API_HASH = "03e024f62a62ecd99bda067e6a2d1824"

DTEK_BOT = "@DTEKKyivRegionElektromerezhiBot"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHANNEL_ID = -1003856095678

STATE_FILE = "state.txt"

GRAPH_FILE = "graph.jpg"
CROP_FILE = "graph_crop.png"

QUEUE_NAME = "Черга 1.2"

# твій перевірений ROI
CROP_X = 0
CROP_Y = 0
CROP_W = 1014
CROP_H = 411

# координата рядка "Сьогодні"
ROW_Y = 200
ROW_HEIGHT = 40


# ================= STATE =================

def get_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_state():
    if not os.path.exists(STATE_FILE):
        return ""
    return open(STATE_FILE).read().strip()


def save_state(h):
    open(STATE_FILE, "w").write(h)


# ================= IMAGE =================

def crop_graph():

    img = cv2.imread(GRAPH_FILE)

    crop = img[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]

    cv2.imwrite(CROP_FILE, crop)

    return crop


def to_monochrome(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, mono = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    return mono


# ================= GRID =================

def find_vertical_lines(mono):

    h, w = mono.shape

    lines = []

    for x in range(w):

        col = mono[:, x]

        dark = np.sum(col == 0)

        if dark > h * 0.3:
            lines.append(x)

    # очистка дублювання
    clean = []
    prev = -100

    for x in lines:
        if x - prev > 5:
            clean.append(x)
            prev = x

    return clean


def build_cells(lines):

    cells = []

    for i in range(len(lines)-1):

        x1 = lines[i]
        x2 = lines[i+1]

        if x2 - x1 > 10:
            cells.append((x1, x2))

    # беремо тільки останні 24
    return cells[-24:]


# ================= ANALYSIS =================

def analyze_cells(img):

    mono = to_monochrome(img)

    lines = find_vertical_lines(mono)

    cells = build_cells(lines)

    outages = []

    for i, (x1, x2) in enumerate(cells):

        cell = mono[ROW_Y:ROW_Y+ROW_HEIGHT, x1:x2]

        w = cell.shape[1]

        left = cell[:, :w//2]
        right = cell[:, w//2:]

        left_dark = np.mean(left) < 200
        right_dark = np.mean(right) < 200

        if left_dark and right_dark:
            outages.append((i, i+1))

        elif left_dark:
            outages.append((i, i+0.5))

        elif right_dark:
            outages.append((i+0.5, i+1))

    return merge_intervals(outages)


def merge_intervals(intervals):

    if not intervals:
        return []

    intervals.sort()

    merged = [intervals[0]]

    for s, e in intervals[1:]:

        ps, pe = merged[-1]

        if s <= pe:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))

    return merged


def format_intervals(intervals):

    result = []

    for s, e in intervals:

        sh = int(s)
        sm = int((s % 1) * 60)

        eh = int(e)
        em = int((e % 1) * 60)

        result.append(f"{sh:02d}:{sm:02d}–{eh:02d}:{em:02d}")

    return result


# ================= TELEGRAM =================

def send_to_channel(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(GRAPH_FILE, "rb") as f:

        requests.post(
            url,
            data={
                "chat_id": CHANNEL_ID,
                "caption": text
            },
            files={"photo": f}
        )


# ================= DTEK =================

async def get_graph():

    async with TelegramClient("session", API_ID, API_HASH) as client:

        bot = await client.get_entity(DTEK_BOT)

        await client.send_message(bot, "Графік відключень")

        await asyncio.sleep(3)

        msgs = await client.get_messages(bot, limit=5)

        for msg in msgs:

            if msg.photo:

                await msg.download_media(GRAPH_FILE)

                return True

    return False


# ================= MAIN =================

async def main():

    print("START")

    ok = await get_graph()

    if not ok:
        print("NO GRAPH")
        return

    h = get_hash(GRAPH_FILE)

    if h == load_state():
        print("NO CHANGE")
        return

    save_state(h)

    img = crop_graph()

    intervals = analyze_cells(img)

    times = format_intervals(intervals)

    now = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%d.%m.%Y %H:%M")

    text = f"{QUEUE_NAME}\n"
    text += f"Оновлено: {now}\n\n"

    if times:
        text += "Сьогодні:\n"
        text += "\n".join(times)
    else:
        text += "Світло є весь день"

    send_to_channel(text)

    print("DONE")


# ================= RUN =================

asyncio.run(main())
