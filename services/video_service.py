import httpx
import asyncio
import os
from config import DID_API_KEY

DID_BASE = "https://api.d-id.com"

async def generate_video_from_summary(summary: str, title: str) -> str:
    """
    Generate a talking avatar video using D-ID API.
    Returns the final video URL or empty string if unavailable.
    """
    if not DID_API_KEY:
        print("⚠️  D-ID API key not set — skipping video generation")
        return ""

    # Trim summary to fit D-ID's limit (max ~1000 chars works well)
    script_text = summary[:900].strip()
    if not script_text:
        return ""

    headers = {
        "Authorization": DID_API_KEY,   # already "Basic ..."
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    try:
        # Step 1: Create the talk (video generation job)
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{DID_BASE}/talks",
                headers=headers,
                json={
                    "script": {
                        "type": "text",
                        "input": script_text,
                        "provider": {
                            "type": "microsoft",
                            "voice_id": "en-US-JennyNeural"
                        }
                    },
                    "source_url": "https://clips-presenters.d-id.com/amy/image.png",
                    # ↑ D-ID's built-in free presenter (no custom avatar needed)
                    "config": {
                        "fluent": True,
                        "pad_audio": 0.0
                    }
                }
            )
            res.raise_for_status()
            talk_id = res.json().get("id")

        if not talk_id:
            print("⚠️  D-ID did not return a talk ID")
            return ""

        print(f"🎬 D-ID job created: {talk_id}")

        # Step 2: Poll for completion (max ~3 mins)
        for attempt in range(36):  # 36 × 5s = 3 mins
            await asyncio.sleep(5)
            async with httpx.AsyncClient(timeout=15) as client:
                status_res = await client.get(
                    f"{DID_BASE}/talks/{talk_id}",
                    headers=headers
                )
                data = status_res.json()
                status = data.get("status")
                print(f"   D-ID status [{attempt+1}/36]: {status}")

                if status == "done":
                    video_url = data.get("result_url", "")
                    print(f"✅ D-ID video ready: {video_url}")
                    return video_url

                elif status in ("error", "rejected"):
                    print(f"❌ D-ID job failed: {data.get('error', data)}")
                    return ""

        print("⏰ D-ID video generation timed out")
        return ""

    except httpx.HTTPStatusError as e:
        print(f"❌ D-ID HTTP error: {e.response.status_code} — {e.response.text}")
        return ""
    except Exception as e:
        print(f"❌ D-ID error: {e}")
        return ""