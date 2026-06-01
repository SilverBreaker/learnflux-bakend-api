import aiosqlite
import os

DB_PATH = "learnflux.db"

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                institution TEXT DEFAULT '',
                plan        TEXT DEFAULT 'free',
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS documents (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                title       TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                size_mb     REAL DEFAULT 0,
                status      TEXT DEFAULT 'pending',
                created_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS ai_results (
                id               TEXT PRIMARY KEY,
                document_id      TEXT UNIQUE NOT NULL,
                summary          TEXT DEFAULT '',
                key_concepts     TEXT DEFAULT '',
                definitions      TEXT DEFAULT '',
                conclusion       TEXT DEFAULT '',
                video_url        TEXT DEFAULT '',
                video_duration   TEXT DEFAULT '',
                mindmap_json     TEXT DEFAULT '{}',
                quiz_json        TEXT DEFAULT '[]',
                imp_questions    TEXT DEFAULT '[]',
                ppt_url          TEXT DEFAULT '',
                updated_at       TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );
        """)
        await db.commit()
    print("✅ Database initialized")