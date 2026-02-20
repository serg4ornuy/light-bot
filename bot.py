import asyncio
import hashlib
import os
import requests

from telethon import TelegramClient

api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

DTEK_BOT = "DTEKKyivRegionElektromerezhiBot"


async def get_schedule():

    client = TelegramClient("session", api_id, api_hash)
    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    # start
    await client.send_message(bot, "/start")
    await asyncio.sleep(3)

    # reply keyboard (обов'язково з emoji)
    await client.send_message(bot, "Графік відключень🕒")
    await asyncio.sleep(3)

    # inline: Наступний >
    msg = await client.get_messages(bot, limit=1)

    if msg[0].buttons:
        await msg[0].click(text="Наступний >")

    await asyncio.sleep(3)

    # inline: Обрати
    msg = await client.get_messages(bot, limit=1)

    if msg[0].buttons:
        await msg[0].click(text="✅ Обрати")

    await asyncio.sleep(5)

    # знайти фото
    messages = await client.get_messages(bot, limit=5)

    file_path = None

    for m in messages:
        if m.photo:
            file_path = "schedule.jpg"
            await m.download_media(file_path)
            break

    await client.disconnect()

    return file_path


def send_photo(path):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(path, "rb") as f:

        requests.post(
            url,
            data={"chat_id": CHAT_ID},
            files={"photo": f}
        )


def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE).read()


def save_state(state):

    open(STATE_FILE, "w").write(state)


async def main():

    path = await get_schedule()

    if not path:
        print("Фото не знайдено")
        return

    data = open(path, "rb").read()

    new_hash = hashlib.md5(data).hexdigest()

    old_hash = load_state()

    if old_hash is None:

        send_photo(path)
        save_state(new_hash)

    elif new_hash != old_hash:

        send_photo(path)
        save_state(new_hash)


asyncio.run(main())
