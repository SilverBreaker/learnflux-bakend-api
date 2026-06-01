import aiosqlite
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from db import get_db
from auth_utils import get_current_user

router = APIRouter()

class ProfileBody(BaseModel):
    name: str
    email: str
    institution: str = ""

# GET /profile
@router.get("/profile")
async def get_profile(
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "name":         row["name"],
        "email":        row["email"],
        "institution":  row["institution"] or "",
        "plan":         row["plan"] or "free",
        "member_since": row["created_at"],
    }

# PUT /profile
@router.put("/profile")
async def update_profile(
    body: ProfileBody,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    await db.execute(
        "UPDATE users SET name = ?, email = ?, institution = ? WHERE id = ?",
        (body.name, body.email, body.institution, user_id)
    )
    await db.commit()
    return {"name": body.name, "email": body.email, "institution": body.institution}

# GET /stats
@router.get("/stats")
async def get_stats(
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute(
        "SELECT COUNT(*) as total FROM documents WHERE user_id = ?", (user_id,)
    ) as cur:
        total = (await cur.fetchone())["total"]

    async with db.execute(
        "SELECT COUNT(*) as ready FROM documents WHERE user_id = ? AND status = 'ready'",
        (user_id,)
    ) as cur:
        ai_ready = (await cur.fetchone())["ready"]

    async with db.execute(
        "SELECT COUNT(*) as vids FROM ai_results ar "
        "JOIN documents d ON d.id = ar.document_id "
        "WHERE d.user_id = ? AND ar.video_url != ''",
        (user_id,)
    ) as cur:
        videos = (await cur.fetchone())["vids"]

    return {
        "total_docs":        total,
        "ai_ready":          ai_ready,
        "videos_generated":  videos,
        "quizzes_taken":     0,  # extend when you add quiz attempt tracking
    }