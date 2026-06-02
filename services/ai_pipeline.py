import json
import aiosqlite
from db import DB_PATH
from services.pdf_extractor import extract_text_from_pdf
from services.ai_service import generate_all
from services.video_service import generate_video_from_summary
from services.pdf_generator import create_summary_pdf, create_questions_pdf

async def run_pipeline(doc_id: str, file_path: str):
    print(f"🚀 Pipeline started for doc: {doc_id}")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        await db.execute(
            "UPDATE documents SET status = 'processing' WHERE id = ?", (doc_id,)
        )
        await db.commit()

        try:
            # Step 1: Extract text
            print("📄 Extracting text...")
            text = extract_text_from_pdf(file_path)
            if not text:
                raise ValueError("Could not extract text from PDF")

            # Step 2: Get doc title
            async with db.execute(
                "SELECT title FROM documents WHERE id = ?", (doc_id,)
            ) as cur:
                row = await cur.fetchone()
            title = row["title"] if row else "Document"

            # Step 3: ONE Gemini call for everything
            print("🤖 Running AI generation (single call)...")
            result = generate_all(text)

            summary_data = result.get("summary", {})
            quiz         = result.get("quiz", [])
            questions    = result.get("imp_questions", [])
            mindmap      = result.get("mindmap", {"nodes": [], "edges": []})

            print(f"   ✅ Summary: {len(summary_data.get('overview', ''))} chars")
            print(f"   ✅ Quiz: {len(quiz)} questions")
            print(f"   ✅ Imp questions: {len(questions)}")
            print(f"   ✅ Mindmap: {len(mindmap.get('nodes', []))} nodes")

            # Step 4: Generate video (optional)
            print("🎬 Generating video...")
            video_url = await generate_video_from_summary(
                summary_data.get("overview", ""), title
            )

            # Step 5: Save to DB
            await db.execute("""
                UPDATE ai_results SET
                    summary        = ?,
                    key_concepts   = ?,
                    definitions    = ?,
                    conclusion     = ?,
                    video_url      = ?,
                    mindmap_json   = ?,
                    quiz_json      = ?,
                    imp_questions  = ?,
                    updated_at     = datetime('now')
                WHERE document_id = ?
            """, (
                summary_data.get("overview", ""),
                summary_data.get("key_concepts", ""),
                summary_data.get("definitions", ""),
                summary_data.get("conclusion", ""),
                video_url,
                json.dumps(mindmap),
                json.dumps(quiz),
                json.dumps(questions),
                doc_id
            ))

            # Step 6: Generate downloadable PDFs
            print("📄 Creating downloadable PDFs...")
            create_summary_pdf(doc_id, title, summary_data)
            create_questions_pdf(doc_id, title, questions)

            # Step 7: Mark ready
            await db.execute(
                "UPDATE documents SET status = 'ready' WHERE id = ?", (doc_id,)
            )
            await db.commit()
            print(f"✅ Pipeline complete for doc: {doc_id}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Pipeline failed for doc {doc_id}: {e}")
            await db.execute(
                "UPDATE documents SET status = 'failed' WHERE id = ?", (doc_id,)
            )
            await db.commit()