from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from app.schemas import ChatRequest, ChatResponse, TranscriptResponse, Analytics
from app.store import new_session, get_session, end_session
from app.llm_client import generate_reply, init_cache_on_startup
from app.analytics import generate_analytics
from app.auth import get_current_user
from app.auth_routes import router as auth_router
from app.database import conversations_collection, bookings_collection
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI(title="Northstar Homes AI Sales Agent")

# --- rate limiting setup ---
def _get_user_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1][:20]
    return get_remote_address(request)

limiter = Limiter(key_func=_get_user_key)
app.state.limiter = limiter

async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please wait a moment before trying again."},
    )

app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.include_router(auth_router)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def startup_event():
    init_cache_on_startup()

@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("15/minute")
async def chat(request: Request, req: ChatRequest, username: str = Depends(get_current_user)):
    session_id = req.session_id
    if not session_id:
        session_id = new_session()
    else:
        try:
            get_session(session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Unknown session_id")

    session = get_session(session_id)
    if session["ended"]:
        raise HTTPException(status_code=400, detail="Conversation already ended")
        
    reply_text, should_end = await generate_reply(session_id, req.message, username)

    await conversations_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {"username": username, "ended": should_end},
            "$push": {
                "messages": {
                    "$each": [
                        {"role": "user", "content": req.message},
                        {"role": "assistant", "content": reply_text},
                    ]
                }
            },
        },
        upsert=True,
    )

    if should_end:
        end_session(session_id)

    return ChatResponse(session_id=session_id, reply=reply_text, ended=should_end)


@app.post("/api/end/{session_id}", response_model=Analytics)
async def end_conversation(session_id: str, username: str = Depends(get_current_user)):
    try:
        session = get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    if not session["ended"]:
        end_session(session_id)

    analytics = generate_analytics(session_id)
    analytics_data = analytics.model_dump()

    await conversations_collection.update_one(
        {"session_id": session_id},
        {"$set": {"ended": True, "analytics": analytics_data}},
        upsert=True,
    )

    # Also save the full analytics onto the bookings collection for this
    # session. If the customer never reached the booking step, no booking
    # document exists yet for this session_id — upsert=True creates one so
    # the analytics still get recorded, with booking-specific fields left
    # blank (they were never captured for that session).
    await bookings_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "session_id": session_id,
                "username": username,
                **analytics_data,
            },
            "$setOnInsert": {
                "name": None,
                "phone": None,
                "date": None,
                "time": None,
                "status": None,
                "confirmation_id": None,
                "reason": None,
                "alternative_slots": None,
                "created_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )

    return analytics


@app.get("/api/analytics/{session_id}", response_model=Analytics)
def get_analytics(session_id: str, username: str = Depends(get_current_user)):
    try:
        get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return generate_analytics(session_id)


@app.get("/api/transcript/{session_id}", response_model=TranscriptResponse)
def get_transcript(session_id: str, username: str = Depends(get_current_user)):
    try:
        session = get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return TranscriptResponse(session_id=session_id, messages=session["messages"], ended=session["ended"])


@app.get("/api/my-conversations")
async def my_conversations(username: str = Depends(get_current_user)):
    cursor = conversations_collection.find({"username": username})
    conversations = await cursor.to_list(length=100)
    for c in conversations:
        c["_id"] = str(c["_id"])
    return conversations