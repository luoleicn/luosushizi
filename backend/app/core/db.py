"""SQLite helpers and schema initialization."""

from __future__ import annotations

import os
import sqlite3
from typing import Iterator


def get_connection(db_path: str) -> sqlite3.Connection:
    if db_path:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hanzi TEXT NOT NULL UNIQUE,
            pinyin TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'offline',
            cached_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS study_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            character_id INTEGER NOT NULL,
            ease_factor REAL NOT NULL DEFAULT 2.5,
            interval INTEGER NOT NULL DEFAULT 0,
            repetitions INTEGER NOT NULL DEFAULT 0,
            last_reviewed_at TEXT,
            next_review_at TEXT,
            last_rating INTEGER,
            UNIQUE(user_id, character_id),
            FOREIGN KEY(character_id) REFERENCES characters(id)
        );

        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            total_cards INTEGER NOT NULL DEFAULT 0,
            known_count INTEGER NOT NULL DEFAULT 0,
            unknown_count INTEGER NOT NULL DEFAULT 0
        );
        """
    )


def iter_rows(conn: sqlite3.Connection, query: str, params: tuple = ()) -> Iterator[sqlite3.Row]:
    cursor = conn.execute(query, params)
    for row in cursor:
        yield row
