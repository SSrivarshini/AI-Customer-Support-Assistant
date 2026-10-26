"""Functional scenario runner. Checks that each message triggers the expected MCP tool.

Run: python -m tests.run_scenarios
Add more entries to tests/scenarios.json to grow coverage.
"""
import asyncio
import json
from pathlib import Path

from app.agent.graph import build_graph
from app.mcp_client import load_mcp_tools

SCENARIOS = json.loads((Path(__file__).parent / "scenarios.json").read_text())


def tools_called(messages) -> set[str]:
    called = set()
    for m in messages:
        for call in getattr(m, "tool_calls", None) or []:
            called.add(call["name"])
    return called


async def main():
    graph = build_graph(await load_mcp_tools())
    passed = 0
    for s in SCENARIOS:
        result = await graph.ainvoke(
            {"messages": [("user", s["input"])]},
            config={"configurable": {"thread_id": s["id"]}},
        )
        called = tools_called(result["messages"])
        expected = s["expect_tool"]
        ok = (expected in called) if expected else not called
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {s['id']}: {s['input']!r} -> {sorted(called) or 'no tools'}")
    print(f"\n{passed}/{len(SCENARIOS)} scenarios passed")


if __name__ == "__main__":
    asyncio.run(main())
