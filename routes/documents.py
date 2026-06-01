import uuid
import os
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from db import get_db
from auth_utils import get_current_user
from config import UPLOAD_DIR
from services.ai_pipeline import run_pipeline

router = APIRouter()

# GET /documents
@router.get("")
async def list_documents(
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute(
        "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]

# POST /documents/upload
@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(None),
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save file to disk
    doc_id    = str(uuid.uuid4())
    file_name = f"{doc_id}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    doc_title = title or file.filename or "Untitled"

    content = await file.read()
    size_mb = round(len(content) / (1024 * 1024), 2)

    with open(file_path, "wb") as f:
        f.write(content)

    # Save document record
    await db.execute(
        "INSERT INTO documents (id, user_id, title, file_path, size_mb, status) VALUES (?, ?, ?, ?, ?, 'pending')",
        (doc_id, user_id, doc_title, file_path, size_mb)
    )
    # Create empty ai_results row
    await db.execute(
        "INSERT INTO ai_results (id, document_id) VALUES (?, ?)",
        (str(uuid.uuid4()), doc_id)
    )
    await db.commit()

    # Kick off AI pipeline in background (non-blocking)
    background_tasks.add_task(run_pipeline, doc_id, file_path)

    return {
        "id": doc_id,
        "title": doc_title,
        "status": "pending",
        "size_mb": size_mb,
        "created_at": "Just now"
    }

# GET /documents/{id}
@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute(
        "SELECT * FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id)
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return dict(row)

# DELETE /documents/{id}
@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute(
        "SELECT file_path FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id)
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    if os.path.exists(row["file_path"]):
        os.remove(row["file_path"])

    await db.execute("DELETE FROM ai_results WHERE document_id = ?", (doc_id,))
    await db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    await db.commit()
    return {"message": "Document deleted"}