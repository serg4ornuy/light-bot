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

ADDRESS = "Богуслав, Росьова, 70"


async def get_schedule():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    bot = await client.get_entity(DTEK_BOT)

    # надіслати адресу
    await client.send_message(bot, ADDRESS)

    # чекати відповідь
    await asyncio.sleep(5)

    messages = await client.get_messages(bot, limit=1)

    await client.disconnect()

    return messages[0].text


def send_to_channel(text):

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE).read()


def save_state(state):

    open(STATE_FILE, "w").write(state)


async def main():

    text = await get_schedule()

    new_hash = hashlib.md5(text.encode()).hexdigest()

    old_hash = load_state()

    if old_hash is None:

        send_to_channel("✅ Графік отримано\n\n" + text)

        save_state(new_hash)

    elif new_hash != old_hash:

        send_to_channel("⚡ Графік змінено\n\n" + text)

        save_state(new_hash)


asyncio.run(main())
