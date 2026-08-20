import uuid
from typing import Dict, Any


SESSIONS: Dict[str, Dict[str, Any]] = {}


def new_session() -> str:
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "messages": [],       # list of {"role": "user"/"assistant", "content": str}
        "state": {
            "name": None,
            "phone": None,
            "configuration_interest": None,
            "budget_signal": None,
            "timeline": None,
            "purpose": None,
            "language_used": "unknown",
            "objections_raised": [],
            "site_visit": {"status": "not_discussed", "date": None, "time": None},
            "escalated_to_human": False,
            "do_not_contact": False,
            "follow_up_required": False,
            "follow_up_note": None,
        },
        "ended": False,
    }
    return session_id


def get_session(session_id: str) -> Dict[str, Any]:
    if session_id not in SESSIONS:
        raise KeyError(f"Unknown session_id: {session_id}")
    return SESSIONS[session_id]


def add_message(session_id: str, role: str, content: str) -> None:
    SESSIONS[session_id]["messages"].append({"role": role, "content": content})


def end_session(session_id: str) -> None:
    SESSIONS[session_id]["ended"] = True
