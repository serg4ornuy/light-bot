import asyncio
import hashlib
import os
import requests

from telethon import TelegramClient

# твої API
api_id = 37132117
api_hash = "03e024f62a62ecd99bda067e6a2d1824"

# твій Telegram бот
BOT_TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

DTEK_BOT = "DTEKKyivRegionElektromerezhiBot"


async def get_dtek_message():

    client = TelegramClient("session", api_id, api_hash)

    await client.start()

    entity = await client.get_entity(DTEK_BOT)

    messages = await client.get_messages(entity, limit=1)

    await client.disconnect()

    return messages[0].text


def send_to_channel(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


def load_state():

    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as f:
        return f.read()


def save_state(state):

    with open(STATE_FILE, "w") as f:
        f.write(state)


async def main():

    text = await get_dtek_message()

    new_hash = hashlib.md5(text.encode()).hexdigest()

    old_hash = load_state()

    if old_hash is None:

        send_to_channel(
            "✅ Підключено до DTEK\n\n" + text
        )

        save_state(new_hash)

    elif new_hash != old_hash:

        send_to_channel(
            "⚡ Графік оновлено\n\n" + text
        )

        save_state(new_hash)


asyncio.run(main())
