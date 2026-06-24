import uuid
import os
import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from auth_utils import get_current_user
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


def _fetch_via_youtube_transcript_api(video_id: str) -> str | None:
    """Try youtube-transcript-api first."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt = YouTubeTranscriptApi()
        data = ytt.fetch(video_id)
        return " ".join([t.text for t in data])
    except Exception as e:
        print(f"[transcript-api primary] {e}")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)
        for transcript in transcript_list:
            try:
                data = transcript.fetch()
                return " ".join([t.text for t in data])
            except Exception:
                continue
    except Exception as e:
        print(f"[transcript-api list] {e}")

    return None


def _fetch_via_ytdlp(video_id: str) -> str | None:
    """Fallback: use yt-dlp to extract subtitles."""
    try:
        import yt_dlp
        import tempfile

        url = f"https://www.youtube.com/watch?v={video_id}"
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'subtitlesformat': 'vtt',
                'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find the downloaded subtitle file
            for fname in os.listdir(tmpdir):
                if fname.endswith('.vtt'):
                    fpath = os.path.join(tmpdir, fname)
                    with open(fpath, 'r', encoding='utf-8') as f:
                        raw = f.read()
                    # Strip VTT formatting
                    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> .*', '', raw)
                    text = re.sub(r'<[^>]+>', '', text)
                    text = re.sub(r'WEBVTT.*?\n', '', text)
                    text = re.sub(r'\n+', ' ', text).strip()
                    if len(text) > 50:
                        return text
    except Exception as e:
        print(f"[yt-dlp] {e}")

    return None


def _fetch_transcript(video_id: str) -> str:
    # Try youtube-transcript-api first
    result = _fetch_via_youtube_transcript_api(video_id)
    if result:
        return result

    # Fallback to yt-dlp
    result = _fetch_via_ytdlp(video_id)
    if result:
        return result

    raise HTTPException(
        status_code=400,
        detail="Could not fetch transcript. The video may have no captions, or is restricted."
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
@router.get("/download/{job_id}")
async def download_youtube_pdf(job_id: str):
    path = f"outputs/summary_{job_id}.pdf"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path, media_type="application/pdf", filename="youtube_notes.pdf")