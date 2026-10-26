import httpx

from app.config import TELEGRAM_BOT_TOKEN

API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def send_message(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text})


async def send_typing(chat_id: int) -> None:
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(f"{API}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})
