import asyncio
import hashlib
import os
import requests
import re

from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient


# =========================
# TELEGRAM CONFIG
# =========================

api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

DTEK_BOT = "DTEKKyivRegionElektromerezhiBot"

QUEUE = "1.2"

STATE_FILE = "state.txt"


# =========================
# TIME
# =========================

def now_kyiv():

    return datetime.now(ZoneInfo("Europe/Kyiv"))


# =========================
# PARSE INTERVALS
# =========================

def parse_intervals(text):

    intervals = re.findall(
        r'(\d{2}):(\d{2})-(\d{2}):(\d{2})',
        text
    )

    parsed = []

    for h1, m1, h2, m2 in intervals:

        start = int(h1) * 60 + int(m1)
        end = int(h2) * 60 + int(m2)

        parsed.append((start, end))

    parsed.sort()

    return parsed


# =========================
# STATUS + NEXT OUTAGE
# =========================

def build_status(text):

    now = now_kyiv()

    now_minutes = now.hour * 60 + now.minute

    intervals = parse_intervals(text)

    status_line = "Світло є 💡"

    next_outage = None

    # перевірка чи зараз без світла
    for start, end in intervals:

        if start <= now_minutes <= end:

            end_h = end // 60
            end_m = end % 60

            status_line = f"Світла немає до {end_h:02}:{end_m:02} 🕯️"

            # знайти наступне відключення після включення
            future = [i for i in intervals if i[0] > end]

            if future:

                next_start = future[0][0]

                next_outage = f"{next_start//60:02}:{next_start%60:02}"

            break

    else:
        # світло є → знайти найближче відключення
        future = [i for i in intervals if i[0] > now_minutes]

        if future:

            next_start = future[0][0]

            status_line = f"Світло є до {next_start//60:02}:{next_start%60:02} 💡"

            next_outage = f"{next_start//60:02}:{next_start%60:02}"

    return status_line, next_outage


# =========================
# CAPTION
# =========================

def build_caption(text):

    status_line, next_outage = build_status(text)

    now = now_kyiv().strftime("%d.%m.%Y %H:%M")

    caption = status_line + "\n"

    if next_outage:

        caption += f"Наступне відключення: {next_outage}\n"

    caption += f"Черга {QUEUE}\n"

    caption += f"Оновлено: {now}"

    return caption


# =========================
# GET PHOTO FROM DTEK BOT
# =========================

async def get_schedule():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    await client.send_message(bot, "/start")

    await asyncio.sleep(2)

    await client.send_message(bot, "Графік відключень🕒")

    await asyncio.sleep(3)

    msg = await client.get_messages(bot, limit=1)

    if msg[0].buttons:

        await msg[0].click(text="Наступний >")

    await asyncio.sleep(2)

    msg = await client.get_messages(bot, limit=1)

    if msg[0].buttons:

        await msg[0].click(text="✅ Обрати")

    await asyncio.sleep(5)

    messages = await client.get_messages(bot, limit=5)

    file_path = None
    text = ""

    for m in messages:

        if m.photo:

            file_path = "schedule.jpg"

            await m.download_media(file_path)

            text = m.text or ""

            break

    await client.disconnect()

    return file_path, text


# =========================
# SEND PHOTO
# =========================

def send_photo(path, text):

    caption = build_caption(text)

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


# =========================
# STATE
# =========================

def load_state():

    if not os.path.exists(STATE_FILE):

        return None

    return open(STATE_FILE).read()


def save_state(state):

    open(STATE_FILE, "w").write(state)


# =========================
# MAIN
# =========================

async def main():

    path, text = await get_schedule()

    if not path:

        print("Фото не знайдено")

        return

    data = open(path, "rb").read()

    new_hash = hashlib.md5(data).hexdigest()

    old_hash = load_state()

    if old_hash is None:

        send_photo(path, text)

        save_state(new_hash)

    elif new_hash != old_hash:

        send_photo(path, text)

        save_state(new_hash)


asyncio.run(main())
