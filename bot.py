import asyncio
import hashlib
import os
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient


# =========================
# CONFIG
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
# CAPTION
# =========================

def build_caption():

    now = now_kyiv().strftime("%d.%m.%Y %H:%M")

    return (
        f"Черга {QUEUE}\n"
        f"Оновлено: {now}"
    )


# =========================
# SEND PHOTO
# =========================

def send_photo(path):

    caption = build_caption()

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

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def save_state(state):

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(state)


# =========================
# GET GRAPH FROM DTEK BOT
# =========================

async def get_graph():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    # start
    await client.send_message(bot, "/start")

    await asyncio.sleep(2)

    # reply keyboard
    await client.send_message(bot, "Графік відключень🕒")

    await asyncio.sleep(3)

    # inline: Наступний >
    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:
        await msg[0].click(text="Наступний >")

    await asyncio.sleep(2)

    # inline: Обрати
    msg = await client.get_messages(bot, limit=1)

    if msg and msg[0].buttons:
        await msg[0].click(text="✅ Обрати")

    await asyncio.sleep(5)

    # знайти фото і текст
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


# =========================
# MAIN
# =========================

async def main():

    file_path, graph_text = await get_graph()

    if not file_path:
        print("Фото не знайдено")
        return

    # hash від тексту, НЕ фото
    new_hash = hashlib.md5(graph_text.encode("utf-8")).hexdigest()

    old_hash = load_state()

    if old_hash is None:

        send_photo(file_path)

        save_state(new_hash)

        print("Перше відправлення")

    elif new_hash != old_hash:

        send_photo(file_path)

        save_state(new_hash)

        print("Графік змінився — відправлено")

    else:

        print("Графік без змін")


# =========================

asyncio.run(main())
