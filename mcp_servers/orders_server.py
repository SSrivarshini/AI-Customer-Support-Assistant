"""MCP server: order lookup + support-request workflows backed by MySQL."""
from datetime import date

from mcp.server.fastmcp import FastMCP

from db import get_conn

mcp = FastMCP("orders")

# Predefined business rules: issue type -> (team, default priority)
ROUTING_RULES = {
    "damaged": ("returns_team", "high"),
    "delayed": ("logistics_team", "medium"),
    "wrong_item": ("returns_team", "medium"),
    "other": ("general_support", "low"),
}
DELAY_ESCALATION_DAYS = 3


def _fetch_order(order_id: str):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM orders WHERE order_id = %s", (order_id.upper(),))
        return cur.fetchone()
    finally:
        conn.close()


def _serialize(row: dict) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row.items()}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """Get the current status and details of an order by its order ID (e.g. ORD1001)."""
    order = _fetch_order(order_id)
    if not order:
        return {"found": False, "message": f"No order found with ID {order_id}."}
    return {"found": True, **_serialize(order)}


@mcp.tool()
def get_delivery_update(order_id: str) -> dict:
    """Get delivery tracking info (carrier, tracking number, location, ETA, days overdue)."""
    order = _fetch_order(order_id)
    if not order:
        return {"found": False, "message": f"No order found with ID {order_id}."}
    overdue = 0
    if order["status"] != "delivered":
        overdue = max((date.today() - order["expected_delivery"]).days, 0)
    return {
        "found": True,
        "order_id": order["order_id"],
        "status": order["status"],
        "carrier": order["carrier"],
        "tracking_number": order["tracking_number"],
        "last_location": order["last_location"],
        "expected_delivery": order["expected_delivery"].isoformat(),
        "days_overdue": overdue,
    }


@mcp.tool()
def report_order_issue(order_id: str, issue_type: str, description: str) -> dict:
    """Create a support request for an order issue.

    issue_type must be one of: damaged, delayed, wrong_item, other.
    The request is routed to a team and prioritised using predefined business rules.
    """
    issue_type = issue_type.lower()
    if issue_type not in ROUTING_RULES:
        issue_type = "other"
    order = _fetch_order(order_id)
    if not order:
        return {"created": False, "message": f"No order found with ID {order_id}."}

    team, priority = ROUTING_RULES[issue_type]
    if issue_type == "delayed":
        overdue = (date.today() - order["expected_delivery"]).days
        if overdue >= DELAY_ESCALATION_DAYS:
            priority = "high"

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO support_requests (order_id, issue_type, description, assigned_team, priority) "
            "VALUES (%s, %s, %s, %s, %s)",
            (order["order_id"], issue_type, description, team, priority),
        )
        conn.commit()
        return {
            "created": True,
            "request_id": cur.lastrowid,
            "order_id": order["order_id"],
            "issue_type": issue_type,
            "assigned_team": team,
            "priority": priority,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
