from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from app.agent import prompts
from app.config import LLM_MODEL


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    intent: str


class Intent(BaseModel):
    intent: Literal["order_status", "order_issue", "appointment", "general"]


def build_graph(mcp_tools):
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    tools = {t.name: t for t in mcp_tools}

    def pick(*names):
        return [tools[n] for n in names if n in tools]

    classifier = llm.with_structured_output(Intent)

    def classify(state: State):
        result = classifier.invoke(
            [SystemMessage(prompts.CLASSIFIER_PROMPT), *state["messages"][-6:]]
        )
        return {"intent": result.intent}

    def route(state: State) -> str:
        return state["intent"]

    order_status_agent = create_react_agent(
        llm, pick("get_order_status", "get_delivery_update"), prompt=prompts.ORDER_STATUS_PROMPT
    )
    order_issue_agent = create_react_agent(
        llm, pick("get_order_status", "report_order_issue"), prompt=prompts.ORDER_ISSUE_PROMPT
    )
    appointment_agent = create_react_agent(
        llm, pick("check_availability", "book_appointment"), prompt=prompts.APPOINTMENT_PROMPT
    )
    general_agent = create_react_agent(llm, [], prompt=prompts.GENERAL_PROMPT)

    g = StateGraph(State)
    g.add_node("classify", classify)
    g.add_node("order_status", order_status_agent)
    g.add_node("order_issue", order_issue_agent)
    g.add_node("appointment", appointment_agent)
    g.add_node("general", general_agent)

    g.add_edge(START, "classify")
    g.add_conditional_edges(
        "classify",
        route,
        {k: k for k in ["order_status", "order_issue", "appointment", "general"]},
    )
    for node in ["order_status", "order_issue", "appointment", "general"]:
        g.add_edge(node, END)

    # MemorySaver keeps per-chat history (thread_id = Telegram chat id).
    # Swap for a MySQL/Postgres checkpointer in production.
    return g.compile(checkpointer=MemorySaver())
