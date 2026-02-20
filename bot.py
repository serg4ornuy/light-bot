import asyncio
import hashlib
import os
import requests
import re
from datetime import datetime

from telethon import TelegramClient

# Telegram API
api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

# твій бот
BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

# файл стану
STATE_FILE = "state.txt"

# DTEK бот
DTEK_BOT = "DTEKKyivRegionElektromerezhiBot"

# твоя черга
QUEUE = "1.2"


# =========================
# Визначення статусу
# =========================

def parse_status(text):

    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute

    intervals = re.findall(r'(\d{2}):(\d{2})-(\d{2}):(\d{2})', text)

    parsed = []

    for h1, m1, h2, m2 in intervals:

        start = int(h1) * 60 + int(m1)
        end = int(h2) * 60 + int(m2)

        parsed.append((start, end))

    parsed.sort()

    # якщо зараз без світла
    for start, end in parsed:

        if start <= now_minutes <= end:

            end_h = end // 60
            end_m = end % 60

            return f"Світла немає до {end_h:02}:{end_m:02} 🕯️"

    # якщо світло є — шукаємо наступне відключення
    for start, end in parsed:

        if now_minutes < start:

            start_h = start // 60
            start_m = start % 60

            return f"Світло є до {start_h:02}:{start_m:02} 💡"

    return "Світло є 💡"


# =========================
# Формування підпису
# =========================

def build_caption(text):

    status = parse_status(text)

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    return (
        f"{status}\n"
        f"Черга {QUEUE}\n"
        f"Оновлено: {now}"
    )


# =========================
# Отримання фото з DTEK
# =========================

async def get_schedule():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    # старт
    await client.send_message(bot, "/start")
    await asyncio.sleep(2)

    # кнопка графіка (reply keyboard)
    await client.send_message(bot, "Графік відключень🕒")
    await asyncio.sleep(3)

    # кнопка Наступний >
    msg = await client.get_messages(bot, limit=1)

    if msg[0].buttons:
        await msg[0].click(text="Наступний >")

    await asyncio.sleep(2)

    # кнопка Обрати
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
# Відправка фото
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
# State management
# =========================

def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as f:
        return f.read()


def save_state(state):

    with open(STATE_FILE, "w") as f:
        f.write(state)


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
