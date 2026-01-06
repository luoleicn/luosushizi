"""Migrate legacy single character table to per-user dictionaries."""

import argparse
import sqlite3
from typing import Dict, List, Tuple

from app.core.config import get_config_path, load_config
from app.core.db import get_connection


DEFAULT_DICT_NAME = "我的字库"
DEFAULT_VISIBILITY = "private"


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS dictionaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'private',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(owner_id, name)
        );

        CREATE TABLE IF NOT EXISTS characters_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dictionary_id INTEGER NOT NULL,
            hanzi TEXT NOT NULL,
            pinyin TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'offline',
            cached_at TEXT NOT NULL,
            UNIQUE(dictionary_id, hanzi),
            FOREIGN KEY(dictionary_id) REFERENCES dictionaries(id)
        );

        CREATE TABLE IF NOT EXISTS study_records_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            dictionary_id INTEGER NOT NULL,
            character_id INTEGER NOT NULL,
            ease_factor REAL NOT NULL DEFAULT 2.5,
            interval INTEGER NOT NULL DEFAULT 0,
            repetitions INTEGER NOT NULL DEFAULT 0,
            last_reviewed_at TEXT,
            next_review_at TEXT,
            last_rating INTEGER,
            UNIQUE(user_id, dictionary_id, character_id),
            FOREIGN KEY(character_id) REFERENCES characters_new(id),
            FOREIGN KEY(dictionary_id) REFERENCES dictionaries(id)
        );

        CREATE TABLE IF NOT EXISTS study_sessions_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            dictionary_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            total_cards INTEGER NOT NULL DEFAULT 0,
            known_count INTEGER NOT NULL DEFAULT 0,
            unknown_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(dictionary_id) REFERENCES dictionaries(id)
        );
        """
    )


def load_legacy_characters(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute("SELECT id, hanzi, pinyin, source, cached_at FROM characters").fetchall()


def load_user_character_ids(conn: sqlite3.Connection, user_id: str) -> List[int]:
    rows = conn.execute(
        "SELECT DISTINCT character_id AS cid FROM study_records WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    return [row["cid"] for row in rows]


def create_dictionary(conn: sqlite3.Connection, user_id: str, now: str) -> int:
    cursor = conn.execute(
        """
        INSERT INTO dictionaries (owner_id, name, visibility, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, DEFAULT_DICT_NAME, DEFAULT_VISIBILITY, now, now),
    )
    return cursor.lastrowid


def insert_character(
    conn: sqlite3.Connection, dictionary_id: int, row: sqlite3.Row
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO characters_new (dictionary_id, hanzi, pinyin, source, cached_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (dictionary_id, row["hanzi"], row["pinyin"], row["source"], row["cached_at"]),
    )
    return cursor.lastrowid


def migrate(
    conn: sqlite3.Connection,
    users: List[str],
    mode: str,
    now: str,
) -> None:
    characters = load_legacy_characters(conn)
    if not characters:
        return

    for user_id in users:
        dict_id = create_dictionary(conn, user_id, now)
        if mode == "studied":
            user_char_ids = set(load_user_character_ids(conn, user_id))
            selected = [row for row in characters if row["id"] in user_char_ids]
        else:
            selected = characters

        mapping = {}
        for row in selected:
            new_id = insert_character(conn, dict_id, row)
            mapping[row["id"]] = new_id

        sr_rows = conn.execute(
            """
            SELECT user_id, character_id, ease_factor, interval, repetitions,
                   last_reviewed_at, next_review_at, last_rating
            FROM study_records
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()

        for sr in sr_rows:
            new_char_id = mapping.get(sr["character_id"])
            if not new_char_id:
                continue
            conn.execute(
                """
                INSERT INTO study_records_new (
                    user_id, dictionary_id, character_id, ease_factor, interval, repetitions,
                    last_reviewed_at, next_review_at, last_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sr["user_id"],
                    dict_id,
                    new_char_id,
                    sr["ease_factor"],
                    sr["interval"],
                    sr["repetitions"],
                    sr["last_reviewed_at"],
                    sr["next_review_at"],
                    sr["last_rating"],
                ),
            )

        ss_rows = conn.execute(
            """
            SELECT user_id, started_at, ended_at, total_cards, known_count, unknown_count
            FROM study_sessions
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()
        for ss in ss_rows:
            conn.execute(
                """
                INSERT INTO study_sessions_new (
                    user_id, dictionary_id, started_at, ended_at,
                    total_cards, known_count, unknown_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ss["user_id"],
                    dict_id,
                    ss["started_at"],
                    ss["ended_at"],
                    ss["total_cards"],
                    ss["known_count"],
                    ss["unknown_count"],
                ),
            )


def finalize(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        ALTER TABLE characters RENAME TO characters_legacy;
        ALTER TABLE study_records RENAME TO study_records_legacy;
        ALTER TABLE study_sessions RENAME TO study_sessions_legacy;

        ALTER TABLE characters_new RENAME TO characters;
        ALTER TABLE study_records_new RENAME TO study_records;
        ALTER TABLE study_sessions_new RENAME TO study_sessions;

        CREATE INDEX IF NOT EXISTS idx_characters_dict ON characters(dictionary_id);
        CREATE INDEX IF NOT EXISTS idx_study_records_user ON study_records(user_id);
        CREATE INDEX IF NOT EXISTS idx_study_records_dict ON study_records(dictionary_id);
        CREATE INDEX IF NOT EXISTS idx_study_sessions_user ON study_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_study_sessions_dict ON study_sessions(dictionary_id);
        """
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate to per-user dictionaries.")
    parser.add_argument(
        "--mode",
        choices=["all", "studied"],
        default="all",
        help="all: copy all legacy characters to each user's dictionary; studied: only copy characters with records",
    )
    args = parser.parse_args()

    settings = load_config(get_config_path())
    users = [account.username for account in settings.accounts]
    conn = get_connection(settings.sqlite.path)
    try:
        if table_exists(conn, "dictionaries"):
            raise RuntimeError("Migration already applied (dictionaries table exists).")
        create_tables(conn)
        now = conn.execute("SELECT datetime('now') AS now").fetchone()["now"]
        migrate(conn, users, args.mode, now)
        finalize(conn)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
