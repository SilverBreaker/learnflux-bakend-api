import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from db import get_db
from auth_utils import create_token
import aiosqlite

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SignupBody(BaseModel):
    name: str
    email: str
    password: str

class LoginBody(BaseModel):
    email: str
    password: str

# POST /auth/signup
@router.post("/signup")
async def signup(body: SignupBody, db: aiosqlite.Connection = Depends(get_db)):
    # Check if email already exists
    async with db.execute("SELECT id FROM users WHERE email = ?", (body.email,)) as cur:
        if await cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    hashed = pwd.hash(body.password)

    await db.execute(
        "INSERT INTO users (id, name, email, password) VALUES (?, ?, ?, ?)",
        (user_id, body.name, body.email, hashed)
    )
    await db.commit()

    token = create_token(user_id)
    return {
        "token": token,
        "user": {"id": user_id, "name": body.name, "email": body.email, "institution": ""}
    }

# POST /auth/login
@router.post("/login")
async def login(body: LoginBody, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM users WHERE email = ?", (body.email,)) as cur:
        row = await cur.fetchone()

    if not row or not pwd.verify(body.password, row["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(row["id"])
    return {
        "token": token,
        "user": {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "institution": row["institution"] or ""
        }
    }