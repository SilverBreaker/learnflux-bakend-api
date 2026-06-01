import json
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from db import get_db
from auth_utils import get_current_user

router = APIRouter()

async def _get_ai(doc_id: str, user_id: str, db: aiosqlite.Connection) -> dict:
    """Helper: verify doc ownership then fetch ai_results row."""
    async with db.execute(
        "SELECT id FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id)
    ) as cur:
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Document not found")

    async with db.execute(
        "SELECT * FROM ai_results WHERE document_id = ?", (doc_id,)
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="AI results not ready yet")
    return dict(row)

# GET /documents/{id}/summary
@router.get("/{doc_id}/summary")
async def get_summary(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    ai = await _get_ai(doc_id, user_id, db)
    return {
        "overview":      ai["summary"],
        "key_concepts":  ai["key_concepts"],
        "definitions":   ai["definitions"],
        "conclusion":    ai["conclusion"],
    }

# GET /documents/{id}/video
@router.get("/{doc_id}/video")
async def get_video(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    ai = await _get_ai(doc_id, user_id, db)
    if not ai["video_url"]:
        raise HTTPException(status_code=202, detail="Video is still being generated")
    return {
        "video_url": ai["video_url"],
        "duration":  ai["video_duration"],
        "chapters":  [],  # extend when Pictory supports chapters
    }

# GET /documents/{id}/mindmap
@router.get("/{doc_id}/mindmap")
async def get_mindmap(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    ai = await _get_ai(doc_id, user_id, db)
    mindmap = json.loads(ai["mindmap_json"] or "{}")
    return mindmap  # { nodes: [{id, label}], edges: [{from, to}] }

# GET /documents/{id}/quiz
@router.get("/{doc_id}/quiz")
async def get_quiz(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    ai = await _get_ai(doc_id, user_id, db)
    questions = json.loads(ai["quiz_json"] or "[]")
    return {"questions": questions}  # [{q, options:[str], correct:int}]

# GET /documents/{id}/questions
@router.get("/{doc_id}/questions")
async def get_questions(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    ai = await _get_ai(doc_id, user_id, db)
    questions = json.loads(ai["imp_questions"] or "[]")
    return {"questions": questions}  # [str]

# GET /documents/{id}/download/summary-pdf
@router.get("/{doc_id}/download/summary-pdf")
async def download_summary_pdf(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    await _get_ai(doc_id, user_id, db)
    path = f"outputs/summary_{doc_id}.pdf"
    if not __import__("os").path.exists(path):
        raise HTTPException(status_code=404, detail="Summary PDF not generated yet")
    return FileResponse(path, media_type="application/pdf", filename="summary.pdf")

# GET /documents/{id}/download/questions-pdf
@router.get("/{doc_id}/download/questions-pdf")
async def download_questions_pdf(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    await _get_ai(doc_id, user_id, db)
    path = f"outputs/questions_{doc_id}.pdf"
    if not __import__("os").path.exists(path):
        raise HTTPException(status_code=404, detail="Questions PDF not generated yet")
    return FileResponse(path, media_type="application/pdf", filename="questions.pdf")