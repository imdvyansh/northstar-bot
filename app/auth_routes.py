from fastapi import APIRouter, HTTPException, status
from app.database import users_collection
from app.auth import hash_password, verify_password, create_access_token
from app.schemas import UserSignup, UserLogin, Token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=Token)
async def signup(user: UserSignup):
    existing = await users_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed = hash_password(user.password)
    await users_collection.insert_one({
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed,
    })

    token = create_access_token({"sub": user.username})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})
    return Token(access_token=token)