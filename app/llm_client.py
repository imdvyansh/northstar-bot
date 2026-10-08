import os
import json
import time
from typing import Tuple, Optional

from app.prompt import SYSTEM_PROMPT
from app.store import get_session
from app.booking import simulate_booking
from app import mock_agent

MODEL = "openai/gpt-oss-120b"
MAX_HISTORY_TURNS = 8

_client = None


def _use_real_llm() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def _get_client():
    global _client
    if _client is None:
        from groq import AsyncGroq
        _client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def init_llm_on_startup():
    """Initialize Groq once at startup when a production API key is configured."""
    if _use_real_llm():
        _get_client()


async def generate_reply(session_id: str, user_message: str, username: Optional[str] = None) -> Tuple[str, bool]:
    if not _use_real_llm():
        return await mock_agent.generate_reply(session_id, user_message, username)
    return await _generate_reply_real(session_id, user_message, username)


BOOK_SITE_VISIT_TOOL = {
    "type": "function",
    "function": {
        "name": "book_site_visit",
        "description": (
            "Attempt to book a site visit to Northstar One (Sector 79, Gurugram) for the "
            "customer. Only call this once you have all four fields confirmed with the customer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Requested visit date, as the customer said it"},
                "time": {"type": "string", "description": "Requested visit time window, as the customer said it"},
                "name": {"type": "string", "description": "Customer's name"},
                "phone": {"type": "string", "description": "Customer's phone number"},
            },
            "required": ["date", "time", "name", "phone"],
        },
    },
}


async def _generate_reply_real(session_id: str, user_message: str, username: Optional[str] = None) -> Tuple[str, bool]:
    client = _get_client()

    session = get_session(session_id)
    session["messages"].append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    state = session["state"]
    site_visit = state["site_visit"]
    booking_details = {
        "status": site_visit["status"],
        "date": site_visit["date"],
        "time": site_visit["time"],
        "name": state["name"],
        "phone": state["phone"],
    }
    if any(value for value in booking_details.values() if value != "not_discussed"):
        messages.append({
            "role": "system",
            "content": (
                "Booking details saved by the application (authoritative): "
                f"{json.dumps(booking_details, ensure_ascii=False)}. "
                "Reuse details the customer already provided. A failed status means the "
                "saved time was unavailable, not booked; if the customer picks an offered "
                "alternative time, replace only the time and retain the date, name, and phone."
            ),
        })
    messages.extend(session["messages"][-MAX_HISTORY_TURNS:])

    while True:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[BOOK_SITE_VISIT_TOOL],
            temperature=1,
            max_completion_tokens=2048,
            top_p=1,
            reasoning_effort="medium",
        )
        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        if not tool_calls:
            reply_text = (assistant_message.content or "").strip()
            session["messages"].append({"role": "assistant", "content": reply_text})
            should_end = _looks_like_ending(reply_text)
            return reply_text, should_end

        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [call.model_dump(exclude_none=True) for call in tool_calls],
        })
        for call in tool_calls:
            if call.function.name != "book_site_visit":
                result = {"error": "Unknown tool"}
            else:
                args = json.loads(call.function.arguments)
                result = await simulate_booking(
                    args.get("date"), args.get("time"), args.get("name"), args.get("phone"),
                    session_id=session_id, username=username,
                )
                site_visit = session["state"]["site_visit"]
                site_visit["date"], site_visit["time"] = args.get("date"), args.get("time")
                site_visit["status"] = "booked" if result["success"] else "failed"
                session["state"]["name"] = args.get("name")
                session["state"]["phone"] = args.get("phone")
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps({"result": result}),
            })


def _looks_like_ending(text: str) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in ["have a great day", "take care", "won't reach out again", "good day"])