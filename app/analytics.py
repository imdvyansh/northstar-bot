import os
import json
from typing import Optional

from app.store import get_session
from app.schemas import Analytics

ANALYTICS_SYSTEM_PROMPT = """You are a data-extraction assistant. You will be given the
transcript of a conversation between an AI sales agent (Aanya, Northstar Homes) and a
customer. Extract the following fields and reply with ONLY a single JSON object, no other
text:

{
  "language_used": "English" | "Hindi" | "Hinglish",
  "configuration_interest": "2 BHK" | "3 BHK" | null,
  "budget_signal": short string describing what the customer said about budget, or null,
  "timeline": short string (e.g. "immediate", "3-6 months", "exploring"), or null,
  "purpose": "self-use" | "investment" | null,
  "interest_level": "hot" | "warm" | "cold" | "unknown",
  "objections_raised": [list of short strings, e.g. "price_too_high"],
  "site_visit_status": "booked" | "failed" | "proposed" | "not_discussed",
  "site_visit_datetime": short string or null,
  "escalated_to_human": true | false,
  "do_not_contact": true | false,
  "follow_up_required": true | false,
  "follow_up_note": short string or null,
  "summary": one or two sentence summary of the conversation
}
"""


def _use_real_llm() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def generate_analytics(session_id: str) -> Analytics:
    session = get_session(session_id)
    if _use_real_llm():
        try:
            return _generate_analytics_real(session_id)
        except Exception:
            pass  # fall through to rule-based extraction if the LLM call/parse fails
    return _generate_analytics_from_state(session_id)


def _generate_analytics_real(session_id: str) -> Analytics:
    from google import genai
    from google.genai import types

    session = get_session(session_id)
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in session["messages"])

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=transcript,
        config=types.GenerateContentConfig(
            system_instruction=ANALYTICS_SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )
    data = json.loads(response.text)
    data["session_id"] = session_id
    return Analytics(**data)


def _interest_level(state) -> str:
    if state["do_not_contact"]:
        return "cold"
    if state["site_visit"]["status"] == "booked":
        return "hot"
    if (
        state["configuration_interest"]
        or state["site_visit"]["status"] in ("proposed", "failed")
        or state["escalated_to_human"]
    ):
        return "warm"
    return "unknown"


def _generate_analytics_from_state(session_id: str) -> Analytics:
    session = get_session(session_id)
    state = session["state"]
    sv = state["site_visit"]
    sv_datetime: Optional[str] = None
    if sv.get("date") or sv.get("time"):
        sv_datetime = f"{sv.get('date') or ''} {sv.get('time') or ''}".strip()

    summary_bits = []
    if state["configuration_interest"]:
        summary_bits.append(f"interested in {state['configuration_interest']}")
    if sv["status"] == "booked":
        summary_bits.append(f"site visit booked for {sv_datetime}")
    elif sv["status"] == "failed":
        summary_bits.append("requested slot unavailable, follow-up needed")
    if state["do_not_contact"]:
        summary_bits.append("asked not to be contacted again")
    if state["escalated_to_human"]:
        summary_bits.append("escalated to a human executive")
    if state["follow_up_note"] and sv["status"] not in ("booked", "failed"):
        summary_bits.append(state["follow_up_note"].lower())
    summary = "Customer " + ", ".join(summary_bits) + "." if summary_bits else "General enquiry, no strong signal captured."

    return Analytics(
        session_id=session_id,
        language_used=state["language_used"],
        configuration_interest=state["configuration_interest"],
        budget_signal=state["budget_signal"],
        timeline=state["timeline"],
        purpose=state["purpose"],
        interest_level=_interest_level(state),
        objections_raised=state["objections_raised"],
        site_visit_status=sv["status"],
        site_visit_datetime=sv_datetime,
        escalated_to_human=state["escalated_to_human"],
        do_not_contact=state["do_not_contact"],
        follow_up_required=state["follow_up_required"],
        follow_up_note=state["follow_up_note"],
        summary=summary,
    )
