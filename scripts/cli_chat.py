"""Chat with the agent in the terminal (no Telegram needed). Run: python -m scripts.cli_chat"""
import asyncio

from app.agent.graph import build_graph
from app.mcp_client import load_mcp_tools


async def main():
    graph = build_graph(await load_mcp_tools())
    cfg = {"configurable": {"thread_id": "cli"}}
    print("Support assistant ready. Ctrl+C to quit.\n")
    while True:
        text = input("You: ")
        result = await graph.ainvoke({"messages": [("user", text)]}, config=cfg)
        print("Bot:", result["messages"][-1].content, "\n")


if __name__ == "__main__":
    asyncio.run(main())
