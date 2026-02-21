import asyncio
import os
import hashlib
import requests
from datetime import datetime, timedelta

import cv2
import numpy as np

from telethon import TelegramClient
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest

# =========================
# CONFIG
# =========================

API_ID = 37132117
API_HASH = "03e024f62a62ecd99bda067e6a2d1824"

DTEK_BOT = "@DTEKKyivRegionElektromerezhiBot"

CHANNEL_ID = -1003856095678
BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"

GRAPH_FILE = "graph.jpg"
CROP_FILE = "graph_crop.png"
STATE_FILE = "state.txt"

QUEUE = "Черга 1.2"

# crop area (твій перевірений ROI)
CROP_X = 0
CROP_Y = 0
CROP_W = 1014
CROP_H = 411


# =========================
# UTILS
# =========================

def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_state():
    if not os.path.exists(STATE_FILE):
        return ""
    return open(STATE_FILE).read().strip()


def save_state(h):
    open(STATE_FILE, "w").write(h)


def crop_graph():
    img = cv2.imread(GRAPH_FILE)
    crop = img[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]
    cv2.imwrite(CROP_FILE, crop)
    return crop


# =========================
# GRID DETECTION
# =========================

def find_vertical_lines(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    lines = []

    for x in range(gray.shape[1]):
        col = gray[:, x]
        dark = np.sum(col < 80)

        if dark > gray.shape[0] * 0.3:
            lines.append(x)

    # remove duplicates
    clean = []
    prev = -100

    for x in lines:
        if x - prev > 5:
            clean.append(x)
            prev = x

    return clean


def get_cells(lines):

    cells = []

    for i in range(len(lines)-1):
        x1 = lines[i]
        x2 = lines[i+1]

        if x2 - x1 > 10:
            cells.append((x1, x2))

    return cells


# =========================
# CELL ANALYSIS
# =========================

def analyze_row(img, y):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    lines = find_vertical_lines(img)

    cells = get_cells(lines)

    if len(cells) < 24:
        return []

    cells = cells[-24:]

    outages = []

    for i, (x1, x2) in enumerate(cells):

        cell = gray[y:y+40, x1:x2]

        w = cell.shape[1]

        left = cell[:, :w//2]
        right = cell[:, w//2:]

        left_mean = np.mean(left)
        right_mean = np.mean(right)

        start = i
        end = i+1

        if left_mean < 200 and right_mean < 200:
            outages.append((start, end))

        elif left_mean < 200:
            outages.append((start, start+0.5))

        elif right_mean < 200:
            outages.append((start+0.5, end))

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

    out = []

    for s, e in intervals:

        sh = int(s)
        sm = int((s % 1) * 60)

        eh = int(e)
        em = int((e % 1) * 60)

        out.append(f"{sh:02d}:{sm:02d}–{eh:02d}:{em:02d}")

    return out


# =========================
# TELEGRAM SEND
# =========================

def send_to_channel(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(GRAPH_FILE, "rb") as f:

        files = {"photo": f}

        data = {
            "chat_id": CHANNEL_ID,
            "caption": text
        }

        requests.post(url, data=data, files=files)


# =========================
# GET GRAPH FROM DTEK
# =========================

async def get_graph():

    async with TelegramClient("session", API_ID, API_HASH) as client:

        bot = await client.get_entity(DTEK_BOT)

        await client.send_message(bot, "Графік відключень")

        await asyncio.sleep(2)

        msgs = await client.get_messages(bot, limit=5)

        for msg in msgs:

            if msg.photo:

                path = await msg.download_media(GRAPH_FILE)

                return path


# =========================
# MAIN
# =========================

async def main():

    print("START")

    path = await get_graph()

    if not path:
        print("NO GRAPH")
        return

    h = file_hash(path)

    old = load_state()

    if h == old:
        print("NO CHANGE")
        return

    save_state(h)

    img = crop_graph()

    today_y = 200
    tomorrow_y = 243

    today = format_intervals(analyze_row(img, today_y))
    tomorrow = format_intervals(analyze_row(img, tomorrow_y))

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    text = f"{QUEUE}\nОновлено: {now}\n\n"

    if today:
        text += "Сьогодні:\n"
        text += "\n".join(today)

    if tomorrow:
        text += "\n\nЗавтра:\n"
        text += "\n".join(tomorrow)

    send_to_channel(text)

    print("DONE")


# =========================

asyncio.run(main())
