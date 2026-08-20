import re
from typing import Tuple, Optional

from app.booking import simulate_booking
from app.store import get_session
from app.prompt import PROJECT_FACTS

PRICE_LINE = (
    "2 BHK starts at ₹1.35 crore onwards, aur 3 BHK ₹1.75 crore onwards se start hota hai."
)
PRICE_LINE_EN = "2 BHK starts at ₹1.35 crore onwards, and 3 BHK starts at ₹1.75 crore onwards."

HINDI_CHARS = re.compile(r"[\u0900-\u097F]")
HINGLISH_HINTS = [
    "hai", "nahi", "kya", "chahiye", "mera", "kitna", "kaise", "abhi", "baad",
    "acha", "theek", "kar", "karo", "batao", "dekhna", "budget", "haan",
]

STOP_PHRASES = [
    "stop contacting", "don't call", "do not call", "remove my number",
    "mat karo call", "dobara mat karna", "band karo", "no more calls",
    "stop messaging", "unsubscribe", "don't contact",
]
NOT_INTERESTED_PHRASES = [
    "not interested", "nahi chahiye", "interested nahi", "no interest",
]
BUSY_PHRASES = ["busy right now", "i'm busy", "im busy", "abhi busy", "busy hoon", "can't talk", "cant talk"]
CALL_LATER_PHRASES = ["call later", "call me later", "baad me", "baad mein", "contact me later", "later please"]
PRICE_PHRASES = ["price", "cost", "kitna", "kimat", "budget", "crore", "lakh"]
CONFIG_2BHK = ["2 bhk", "2bhk", "two bhk"]
CONFIG_3BHK = ["3 bhk", "3bhk", "three bhk", "teen bhk"]
OBJECTION_EXPENSIVE = ["too expensive", "too high", "mehenga", "mehnga", "can't afford", "high hai"]
UNKNOWN_Q_MARKERS = {
    "possession": "possession date",
    "rera": "RERA number",
    "discount": "discount / offer",
    "floor plan": "exact floor plan",
    "emi": "loan/EMI details",
    "loan": "loan/EMI details",
    "negotiable": "price negotiability",
    "carpet area": "exact carpet area",
    "amenities": "amenities list",
}
HUMAN_PHRASES = ["talk to a human", "talk to human", "real person", "manager se baat", "agent se baat", "speak to someone"]
SITE_VISIT_PHRASES = ["site visit", "visit karna", "dekhna hai", "book a visit", "schedule a visit", "want to visit"]
GREETING_PHRASES = ["hi", "hello", "hey", "namaste", "namaskar"]
BYE_PHRASES = ["bye", "thanks", "thank you", "dhanyavaad", "ok bye", "theek hai bye", "shukriya"]
PHONE_RE = re.compile(r"\b\d{10}\b")


def detect_language(text: str) -> str:
    if HINDI_CHARS.search(text):
        return "Hindi"
    lower = text.lower()
    if any(h in lower for h in HINGLISH_HINTS):
        return "Hinglish"
    return "English"


def contains_any(text: str, phrases) -> bool:
    lower = text.lower()
    return any(p in lower for p in phrases)


async def generate_reply(session_id: str, user_message: str, username: Optional[str] = None) -> Tuple[str, bool]:
    """Returns (reply_text, should_end). Logs both turns to session['messages']."""
    session = get_session(session_id)
    state = session["state"]
    lower = user_message.lower().strip()
    first_turn = len(session["messages"]) == 0
    session["messages"].append({"role": "user", "content": user_message})
    reply_text, should_end = await _route(session, user_message, lower, first_turn, session_id, username)
    session["messages"].append({"role": "assistant", "content": reply_text})
    return reply_text, should_end


async def _route(session, user_message: str, lower: str, first_turn: bool, session_id: str, username: Optional[str]) -> Tuple[str, bool]:
    state = session["state"]

    lang = detect_language(user_message)
    if lang != "English" or state["language_used"] == "unknown":
        state["language_used"] = lang

    if contains_any(lower, CONFIG_2BHK):
        state["configuration_interest"] = "2 BHK"
    elif contains_any(lower, CONFIG_3BHK):
        state["configuration_interest"] = "3 BHK"

    # hard stop / do-not-contact
    if contains_any(lower, STOP_PHRASES):
        state["do_not_contact"] = True
        state["follow_up_required"] = False
        return (
            "Understood, I won't reach out again. Sorry for the disturbance, and thank you "
            "for your time. Have a good day.",
            True,
        )

    # pending site-visit slot filling
    pending = state.get("pending_ask")
    if pending and not state["do_not_contact"]:
        return await _continue_booking_flow(session, user_message, session_id, username)

    # not interested
    if contains_any(lower, NOT_INTERESTED_PHRASES):
        state["follow_up_required"] = False
        return (
            "No problem at all, thank you for letting me know. Should I check back with you "
            "sometime, or would you prefer I don't reach out again?",
            False,
        )

    # busy right now
    if contains_any(lower, BUSY_PHRASES):
        state["follow_up_required"] = True
        state["follow_up_note"] = "Customer was busy, requested a callback."
        return (
            "No worries, I understand you're busy. When would be a good time for me to "
            "reconnect with you?",
            False,
        )

    # call me later
    if contains_any(lower, CALL_LATER_PHRASES):
        state["follow_up_required"] = True
        state["follow_up_note"] = f"Customer asked to be contacted later: \"{user_message}\""
        return (
            "Sure, I'll follow up with you then. Thanks for your time today, take care!",
            True,
        )

    # human escalation
    if contains_any(lower, HUMAN_PHRASES):
        state["escalated_to_human"] = True
        return (
            "Of course, I'll have a Northstar Homes executive reach out to you shortly. "
            "Could you confirm the best number and time to reach you?",
            False,
        )

    # unknown-fact questions
    for marker, label in UNKNOWN_Q_MARKERS.items():
        if marker in lower:
            state["follow_up_required"] = True
            state["follow_up_note"] = f"Customer asked about {label}, which wasn't available."
            return (
                f"That's a good question, but I don't have the {label} with me right now. "
                "I can have a specialist follow up with the exact details, or note it down and "
                "get back to you — whichever works better for you?",
                False,
            )

    # price / objection
    if contains_any(lower, OBJECTION_EXPENSIVE):
        state["objections_raised"] = list(set(state["objections_raised"] + ["price_too_high"]))
        return (
            "Totally understand — it's a big decision. Could you share what budget range "
            "you're comfortable with? If 3 BHK feels like a stretch, our 2 BHK starting at "
            "₹1.35 crore might be a better fit.",
            False,
        )

    if contains_any(lower, PRICE_PHRASES):
        line = PRICE_LINE if state["language_used"] in ("Hindi", "Hinglish") else PRICE_LINE_EN
        return (
            f"{line} Which configuration were you thinking of — 2 BHK or 3 BHK?",
            False,
        )

    # site visit intent
    if contains_any(lower, SITE_VISIT_PHRASES):
        state["site_visit"]["status"] = "proposed"
        state["pending_ask"] = "date"
        return (
            "I'd be happy to set that up. What date works for you to visit Northstar One in "
            "Sector 79, Gurugram?",
            False,
        )

    # greeting / opener
    if first_turn or contains_any(lower, GREETING_PHRASES):
        cfg_line = ""
        if not state["configuration_interest"]:
            cfg_line = " We have 2 BHK and 3 BHK homes available — are you looking at either of those?"
        return (
            "Hi, this is Aanya from Northstar Homes! I'm reaching out about Northstar One, "
            f"our new project in Sector 79, Gurugram.{cfg_line}",
            False,
        )

    # goodbye
    if contains_any(lower, BYE_PHRASES):
        return ("Thank you for your time today! Have a great day ahead.", True)

    # fallback — keep qualifying
    if not state["timeline"]:
        state["timeline"] = "unspecified-followup"
        return (
            "Got it, thanks for sharing that. Are you looking to buy in the near term, or "
            "just exploring options for now?",
            False,
        )

    return (
        "Thanks for sharing that. Would you like me to set up a site visit to Northstar One "
        "so you can see it in person?",
        False,
    )


async def _continue_booking_flow(session, user_message: str, session_id: str, username: Optional[str]) -> Tuple[str, bool]:
    state = session["state"]
    stage = state["pending_ask"]
    sv = state["site_visit"]

    if stage == "date":
        sv["date"] = user_message.strip()
        state["pending_ask"] = "time"
        return (f"Great, {sv['date']} works. What time window suits you best?", False)

    if stage == "time":
        sv["time"] = user_message.strip()
        state["pending_ask"] = "name"
        return ("Perfect. Could I have your name for the visit booking?", False)

    if stage == "name":
        state["name"] = user_message.strip()
        state["pending_ask"] = "phone"
        return (f"Thanks {state['name']}. And the best 10-digit phone number to reach you on?", False)

    if stage == "phone":
        phone_match = PHONE_RE.search(user_message)
        state["phone"] = phone_match.group(0) if phone_match else user_message.strip()
        state["pending_ask"] = None
        result = await simulate_booking(
            sv["date"], sv["time"], state["name"], state["phone"],
            session_id=session_id, username=username,
        )
        if result["success"]:
            sv["status"] = "booked"
            return (
                f"You're all set — your site visit is confirmed for {sv['date']} at "
                f"{sv['time']} (confirmation ID {result['confirmation_id']}). Thank you, "
                f"{state['name']}, looking forward to hosting you at Northstar One!",
                True,
            )
        else:
            sv["status"] = "failed"
            state["follow_up_required"] = True
            state["follow_up_note"] = (
                f"Booking failed for {sv['date']} {sv['time']} ({result['reason']}); "
                f"offered alternatives {result['alternative_slots']}."
            )
            alts = ", ".join(result["alternative_slots"])
            return (
                f"I'm sorry, that exact slot just got fully booked. Would any of these work "
                f"instead — {alts}? Or I can have a colleague confirm a slot and get back to you.",
                False,
            )

    state["pending_ask"] = None
    return ("Sorry, could you repeat that?", False)