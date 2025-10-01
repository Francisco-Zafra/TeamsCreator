from pathlib import Path
import sqlite3
from contextlib import closing

DB_PATH = Path(__file__).with_name("players.sqlite")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    rit INTEGER NOT NULL,
    tir INTEGER NOT NULL,
    pas INTEGER NOT NULL,
    reg INTEGER NOT NULL,
    def INTEGER NOT NULL,
    fis INTEGER NOT NULL,
    media REAL NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1
);
"""

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with closing(get_conn()) as conn:
        conn.execute(SCHEMA_SQL)
        conn.commit()
