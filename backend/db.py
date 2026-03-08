import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "users.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'active'
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_books (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT NOT NULL,
        authors TEXT NOT NULL,
        publisher TEXT NOT NULL,
        genre TEXT NOT NULL,
        mood TEXT NOT NULL,

        num_pages INTEGER,
        average_rating REAL,
        ratings_count INTEGER DEFAULT 0,

        isbn TEXT UNIQUE,
        description TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()