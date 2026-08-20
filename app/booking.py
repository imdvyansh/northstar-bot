from typing import Optional, Dict, Any
from datetime import datetime, timezone
from app.database import bookings_collection

BLOCKED_TIME_MARKERS = ["9 am", "9am", "09:00", "9:00 am", "9 baje"]


async def simulate_booking(
    date: str,
    time: str,
    name: Optional[str],
    phone: Optional[str],
    session_id: Optional[str] = None,
    username: Optional[str] = None,
) -> Dict[str, Any]:
    time_lower = (time or "").lower()
    is_blocked = any(marker in time_lower for marker in BLOCKED_TIME_MARKERS)

    if is_blocked:
        result = {
            "success": False,
            "reason": "The requested slot is fully booked.",
            "alternative_slots": ["11:00 AM", "3:00 PM", "5:00 PM"],
        }
    else:
        result = {
            "success": True,
            "confirmation_id": f"NS-{abs(hash((date, time, name, phone))) % 100000:05d}",
            "date": date,
            "time": time,
        }

    await bookings_collection.insert_one({
        "session_id": session_id,
        "username": username,
        "name": name,
        "phone": phone,
        "date": date,
        "time": time,
        "status": "booked" if result["success"] else "failed",
        "confirmation_id": result.get("confirmation_id"),
        "reason": result.get("reason"),
        "alternative_slots": result.get("alternative_slots"),
        "created_at": datetime.now(timezone.utc),
    })

    return result