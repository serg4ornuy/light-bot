import requests
import hashlib
import os

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

STATE_FILE = "state.txt"

URL = "https://www.dtek-krem.com.ua/api/shutdowns/search"

payload = {
    "city": "Богуслав",
    "street": "Росьова",
    "house": "70"
}


def get_schedule():

    try:

        r = requests.post(URL, json=payload, timeout=30)

        return r.json()

    except Exception as e:

        return {"error": str(e)}


def format_text(data):

    if "error" in data:

        return "ПОМИЛКА API: " + data["error"]

    if "data" not in data:

        return "Графік не знайдено"

    result = []

    for item in data["data"]:

        date = item.get("date")

        for period in item.get("periods", []):

            result.append(
                f"{date} {period['start']}-{period['end']}"
            )

    return "\n".join(result)


def send(text):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


def load_state():

    if not os.path.exists(STATE_FILE):

        return None

    with open(STATE_FILE) as f:

        return f.read()


def save_state(state):

    with open(STATE_FILE, "w") as f:

        f.write(state)

    os.system("git add state.txt")
    os.system("git commit -m update")
    os.system("git push")


data = get_schedule()

text = format_text(data)

new_hash = hashlib.md5(text.encode()).hexdigest()

old_hash = load_state()

if old_hash is None:

    send("✅ Бот запущено\n\n" + text)
    save_state(new_hash)

elif new_hash != old_hash:

    send("⚡ Оновлення\n\n" + text)
    save_state(new_hash)
