import requests


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    """Send a message via Telegram Bot API. Splits if over 4096 chars."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Telegram max message length is 4096 chars
    chunks = [text[i:i + 4096] for i in range(0, len(text), 4096)]
    for chunk in chunks:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
        }, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram error: {data}")
