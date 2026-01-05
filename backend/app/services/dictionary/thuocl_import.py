"""Import THUOCL word list into SQLite and build character index."""

import argparse
import os
import sqlite3


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS common_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            frequency INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'thuocl'
        );

        CREATE TABLE IF NOT EXISTS character_word_index (
            hanzi TEXT NOT NULL,
            word_id INTEGER NOT NULL,
            UNIQUE(hanzi, word_id),
            FOREIGN KEY(word_id) REFERENCES common_words(id)
        );

        CREATE INDEX IF NOT EXISTS idx_cwi_hanzi ON character_word_index(hanzi);
        CREATE INDEX IF NOT EXISTS idx_cw_frequency ON common_words(frequency);
        """
    )


def iter_thuocl_files(thuocl_dir: str):
    for root, _, files in os.walk(thuocl_dir):
        for name in files:
            if name.startswith("."):
                continue
            path = os.path.join(root, name)
            if os.path.isfile(path):
                yield path


def parse_line(line: str):
    line = line.strip()
    if not line:
        return None, None
    parts = line.split()
    if not parts:
        return None, None
    word = parts[0]
    freq = 0
    if len(parts) > 1:
        try:
            freq = int(parts[1])
        except ValueError:
            freq = 0
    return word, freq


def import_words(conn: sqlite3.Connection, thuocl_dir: str) -> int:
    cursor = conn.cursor()
    count = 0
    for path in iter_thuocl_files(thuocl_dir):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                word, freq = parse_line(line)
                if not word:
                    continue
                cursor.execute(
                    "INSERT OR IGNORE INTO common_words (word, frequency) VALUES (?, ?)",
                    (word, freq),
                )
                count += 1
    conn.commit()
    return count


def build_index(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT id, word FROM common_words")
    rows = cursor.fetchall()
    inserts = 0
    for word_id, word in rows:
        for ch in word:
            cursor.execute(
                "INSERT OR IGNORE INTO character_word_index (hanzi, word_id) VALUES (?, ?)",
                (ch, word_id),
            )
            inserts += 1
    conn.commit()
    return inserts


def main():
    parser = argparse.ArgumentParser(description="Import THUOCL word list into SQLite.")
    parser.add_argument("--db-path", required=True, help="Path to SQLite database file")
    parser.add_argument("--thuocl-dir", required=True, help="Directory containing THUOCL word list files")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.db_path), exist_ok=True)
    conn = sqlite3.connect(args.db_path)
    try:
        init_db(conn)
        imported = import_words(conn, args.thuocl_dir)
        indexed = build_index(conn)
    finally:
        conn.close()

    print(f"Imported lines: {imported}")
    print(f"Indexed entries: {indexed}")


if __name__ == "__main__":
    main()
