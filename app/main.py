import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from app.agent.graph import build_graph
from app.config import TELEGRAM_WEBHOOK_SECRET
from app.mcp_client import load_mcp_tools
from app.telegram_client import send_message, send_typing

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("support-bot")

WELCOME = (
    "Hi! I'm your support assistant. I can:\n"
    "- check order status & delivery updates\n"
    "- raise damaged/delayed order issues\n"
    "- book an appointment with our support team\n\n"
    "How can I help?"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tools = await load_mcp_tools()
    log.info("Loaded MCP tools: %s", [t.name for t in tools])
    app.state.graph = build_graph(tools)
    yield


app = FastAPI(title="AI Customer Support Assistant", lifespan=lifespan)


async def handle_message(graph, chat_id: int, text: str):
    try:
        await send_typing(chat_id)
        result = await graph.ainvoke(
            {"messages": [("user", text)]},
            config={"configurable": {"thread_id": str(chat_id)}},
        )
        reply = result["messages"][-1].content or "Sorry, I couldn't process that."
    except Exception:
        log.exception("Agent failed")
        reply = "Sorry, something went wrong. Please try again in a moment."
    await send_message(chat_id, reply)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(
    request: Request,
    background: BackgroundTasks,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret token")

    update = await request.json()
    message = update.get("message") or {}
    text, chat = message.get("text"), message.get("chat", {})
    if not text or "id" not in chat:
        return {"ok": True}

    if text.startswith("/start"):
        background.add_task(send_message, chat["id"], WELCOME)
    else:
        background.add_task(handle_message, request.app.state.graph, chat["id"], text)
    return {"ok": True}
