from typing import Literal

from mcp.server import MCPServer

Priority = Literal["high", "medium", "low"]

TICKETS = [
    {"id": 1, "title": "Checkout returns 500", "priority": "high", "status": "open"},
    {"id": 2, "title": "Typo on pricing page", "priority": "low", "status": "open"},
    {"id": 3, "title": "Login loop on Safari", "priority": "high", "status": "closed"},
    {"id": 4, "title": "Slow search results", "priority": "medium", "status": "open"},
]

server = MCPServer("tickets")


@server.tool()
def search_tickets(priority: Priority | None = None, status: str = "open", limit: int = 10) -> list[dict]:
    """Returns tickets filtered by priority and status, highest priority first."""
    order = {"high": 0, "medium": 1, "low": 2}
    matches = [t for t in TICKETS if t["status"] == status and priority in (None, t["priority"])]
    return sorted(matches, key=lambda t: order[t["priority"]])[:limit]


@server.resource("tickets://{ticket_id}")
def ticket(ticket_id: int) -> str:
    """One ticket as readable text."""
    found = next(t for t in TICKETS if t["id"] == int(ticket_id))
    return f"#{found['id']} [{found['priority']}/{found['status']}] {found['title']}"


@server.prompt()
def triage_summary(priority: str = "high") -> str:
    """Template for summarizing open tickets of one priority."""
    return f"Call search_tickets with priority={priority} and summarize the open tickets in 3 bullets."


if __name__ == "__main__":
    server.run()
