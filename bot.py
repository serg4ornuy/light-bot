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

    await client.send_message(bot, "/start")
    await asyncio.sleep(3)

    msg = await client.get_messages(bot, limit=1)
    await msg[0].click(text="Графік відключень")
    await asyncio.sleep(3)

    msg = await client.get_messages(bot, limit=1)
    await msg[0].click(text="Наступний >")
    await asyncio.sleep(3)

    msg = await client.get_messages(bot, limit=1)
    await msg[0].click(text="Обрати")
    await asyncio.sleep(5)

    msg = await client.get_messages(bot, limit=1)

    await client.disconnect()

    if msg[0].photo:

        file_path = "schedule.jpg"

        await msg[0].download_media(file_path)

        return file_path

    return None


def send_photo(file_path):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(file_path, "rb") as photo:

        requests.post(
            url,
            data={"chat_id": CHAT_ID},
            files={"photo": photo}
        )


def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE).read()


def save_state(state):

    open(STATE_FILE, "w").write(state)


async def main():

    file_path = await get_schedule()

    if not file_path:
        return

    with open(file_path, "rb") as f:
        data = f.read()

    new_hash = hashlib.md5(data).hexdigest()

    old_hash = load_state()

    if old_hash is None:

        send_photo(file_path)
        save_state(new_hash)

    elif new_hash != old_hash:

        send_photo(file_path)
        save_state(new_hash)


asyncio.run(main())
