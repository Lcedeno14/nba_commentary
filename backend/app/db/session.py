import aiosqlite
import os
from app.core.config import settings

async def get_db():
    db = await aiosqlite.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(settings.DATABASE_URL.replace("sqlite:///", "")) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                hashed_password TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.commit() 