import requests

TOKEN = "8459715913:AAGmSdLh1HGd0j1vsMj-7tHwT6jzqsAqgzs"
CHAT_ID = "-1003856095678"

URL = "https://www.dtek-krem.com.ua/ua/shutdowns"

try:

    r = requests.get(URL, timeout=30)

    status_code = r.status_code

    length = len(r.text)

    message = (
        "ДІАГНОСТИКА\n\n"
        f"Status code: {status_code}\n"
        f"Length: {length}\n"
    )

except Exception as e:

    message = f"ПОМИЛКА:\n{str(e)}"


requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)
