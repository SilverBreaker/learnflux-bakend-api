import uuid
import os
import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from auth_utils import get_current_user
from services.ai_service import summarize_transcript
from services.pdf_generator import create_summary_pdf

router = APIRouter()

class YouTubeBody(BaseModel):
    url: str

def _extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise HTTPException(status_code=400, detail="Invalid YouTube URL")

def _fetch_transcript(video_id: str) -> str:
    try:
        ytt = YouTubeTranscriptApi()
        data = ytt.fetch(video_id)
        return " ".join([t.text for t in data])
    except Exception as e:
        print(f"Transcript error: {e}")
        pass

    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)
        for transcript in transcript_list:
            try:
                data = transcript.fetch()
                return " ".join([t.text for t in data])
            except Exception:
                continue
    except Exception as e:
        print(f"List error: {e}")

    raise HTTPException(
        status_code=400,
        detail="Could not fetch transcript from this video."
    )

# POST /youtube/convert
@router.post("/convert")
async def youtube_to_pdf(
    body: YouTubeBody,
    user_id: str = Depends(get_current_user),
):
    video_id = _extract_video_id(body.url.strip())
    transcript = _fetch_transcript(video_id)

    if len(transcript) < 50:
        raise HTTPException(status_code=400, detail="Not enough content from this video.")

    # Summarize using OpenRouter (free)
    summary = {
    "overview": transcript[:2000],
    "key_concepts": "• Key points extracted directly from video transcript",
    "definitions": "",
    "conclusion": "Refer to the transcript above for complete details."
}

    job_id = str(uuid.uuid4())
    title = f"YouTube Notes — {video_id}"
    create_summary_pdf(job_id, title, summary)

    return {
        "pdf_url":    f"/youtube/download/{job_id}",
        "title":      title,
        "page_count": 2
    }

# GET /youtube/download/{job_id}
# GET /youtube/download/{job_id}
@router.get("/download/{job_id}")
async def download_youtube_pdf(job_id: str):
    path = f"outputs/summary_{job_id}.pdf"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path, media_type="application/pdf", filename="youtube_notes.pdf")