import json
import time
from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

def _ask(prompt: str) -> str:
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"Rate limited, waiting 10s (attempt {attempt+2}/3)...")
                time.sleep(10)
            else:
                raise
    raise Exception("Gemini API failed after 3 retries")


def generate_all(text: str) -> dict:
    prompt = f"""You are an expert educator. Analyze this document and return a single JSON object.
Return ONLY valid JSON. No markdown, no backticks, no explanation.

{{
  "summary": {{
    "overview": "2-3 paragraph overview of the document",
    "key_concepts": "• Concept 1\\n• Concept 2\\n• Concept 3\\n• Concept 4\\n• Concept 5",
    "definitions": "Term 1: definition\\nTerm 2: definition\\nTerm 3: definition",
    "conclusion": "1 paragraph conclusion and key takeaways"
  }},
  "quiz": [
    {{"q": "question text", "options": ["option A", "option B", "option C", "option D"], "correct": 0}},
    {{"q": "question text", "options": ["option A", "option B", "option C", "option D"], "correct": 2}}
  ],
  "imp_questions": [
    "Important exam question 1?",
    "Important exam question 2?"
  ],
  "mindmap": {{
    "nodes": [
      {{"id": "1", "label": "Central Topic"}},
      {{"id": "2", "label": "Subtopic 1"}},
      {{"id": "3", "label": "Subtopic 2"}},
      {{"id": "4", "label": "Subtopic 3"}},
      {{"id": "5", "label": "Subtopic 4"}},
      {{"id": "6", "label": "Subtopic 5"}}
    ],
    "edges": [
      {{"from": "1", "to": "2"}},
      {{"from": "1", "to": "3"}},
      {{"from": "1", "to": "4"}},
      {{"from": "1", "to": "5"}},
      {{"from": "1", "to": "6"}}
    ]
  }}
}}

Rules:
- quiz: exactly 10 multiple choice questions, correct is index 0-3
- imp_questions: exactly 15 exam questions as plain strings
- mindmap: 1 central node + 5 subtopic nodes with edges from center
- Return ONLY the JSON object, nothing else

Document:
{text[:3000]}
"""
    raw = _ask(prompt).strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception as e:
        print(f"JSON parse error: {e}")
        return {
            "summary": {
                "overview": raw[:1000] if raw else "Could not generate summary.",
                "key_concepts": "• Key concepts unavailable",
                "definitions": "",
                "conclusion": ""
            },
            "quiz": [],
            "imp_questions": [],
            "mindmap": {"nodes": [], "edges": []}
        }


def generate_summary(text: str) -> dict:
    return generate_all(text).get("summary", {})

def generate_quiz(text: str) -> list:
    return generate_all(text).get("quiz", [])

def generate_important_questions(text: str) -> list:
    return generate_all(text).get("imp_questions", [])

def generate_mindmap(text: str) -> dict:
    return generate_all(text).get("mindmap", {"nodes": [], "edges": []})


def summarize_transcript(transcript: str) -> dict:
    prompt = f"""You are an expert educator. Summarize this YouTube transcript into study notes.
Return ONLY valid JSON. No markdown, no backticks.

{{
  "overview": "2-3 paragraph overview",
  "key_concepts": "• Point 1\\n• Point 2\\n• Point 3\\n• Point 4\\n• Point 5",
  "definitions": "Term 1: definition\\nTerm 2: definition",
  "conclusion": "1 paragraph conclusion"
}}

Transcript:
{transcript[:3000]}
"""
    raw = _ask(prompt).strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {
            "overview": transcript[:1000],
            "key_concepts": "• Key points from the video",
            "definitions": "",
            "conclusion": "Watch the full video for complete details."
        }