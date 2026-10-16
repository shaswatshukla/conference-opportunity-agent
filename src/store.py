"""Transactional snapshots and durable per-source health."""

import json
import sqlite3


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY, created_at TEXT NOT NULL,
            mode TEXT NOT NULL, payload TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_health (
            source TEXT PRIMARY KEY, empty_streak INTEGER NOT NULL DEFAULT 0
        );
        PRAGMA user_version = 1;
    """)
    return db


def save(db, snapshot):
    with db:
        for status in snapshot["coverage"]:
            if snapshot["mode"] != "live":
                status["empty_streak"] = "not updated in fixture mode"
                continue
            old = db.execute(
                "SELECT empty_streak FROM source_health WHERE source=?", (status["source"],)
            ).fetchone()
            if status["failures"]:
                # Access failures are reported separately, not counted as successful empty runs.
                status["empty_streak"] = old[0] if old else 0
                continue
            count = 0 if status["records"] else (old[0] if old else 0) + 1
            db.execute(
                "INSERT OR REPLACE INTO source_health VALUES (?,?)", (status["source"], count)
            )
            status["empty_streak"] = count
        db.execute(
            "INSERT INTO runs(created_at,mode,payload) VALUES (?,?,?)",
            (snapshot["created_at"], snapshot["mode"], json.dumps(snapshot)),
        )


def latest(db, mode):
    row = db.execute(
        "SELECT payload FROM runs WHERE mode=? ORDER BY id DESC LIMIT 1", (mode,)
    ).fetchone()
    if row is None:
        raise ValueError("No saved run for this mode; run discovery first")
    return json.loads(row[0])
