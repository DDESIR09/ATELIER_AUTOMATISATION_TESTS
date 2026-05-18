"""
Gestion du stockage SQLite des runs de tests.
"""

import sqlite3
import json
import os

# La base SQLite est placée à la racine du projet
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs.db")


def init_db():
    """Crée la table 'runs' si elle n'existe pas encore."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            api TEXT NOT NULL,
            passed INTEGER NOT NULL,
            failed INTEGER NOT NULL,
            error_rate REAL NOT NULL,
            availability INTEGER NOT NULL,
            latency_ms_avg INTEGER NOT NULL,
            latency_ms_p95 INTEGER NOT NULL,
            full_result TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_run(run_data):
    """
    Enregistre un run dans la base.
    :param run_data: dict retourné par run_all_tests()
    :return: l'id du run inséré
    """
    init_db()  # s'assure que la table existe

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    summary = run_data["summary"]
    cursor.execute("""
        INSERT INTO runs (
            timestamp, api, passed, failed, error_rate,
            availability, latency_ms_avg, latency_ms_p95, full_result
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_data["timestamp"],
        run_data["api"],
        summary["passed"],
        summary["failed"],
        summary["error_rate"],
        summary["availability"],
        summary["latency_ms_avg"],
        summary["latency_ms_p95"],
        json.dumps(run_data),  # on stocke aussi le JSON complet pour le détail
    ))

    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def list_runs(limit=50):
    """
    Retourne la liste des derniers runs (du plus récent au plus ancien).
    :param limit: nombre maximum de runs à retourner
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # pour avoir des dicts au lieu de tuples
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, api, passed, failed, error_rate,
               availability, latency_ms_avg, latency_ms_p95
        FROM runs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_last_run():
    """Retourne le dernier run complet (avec le détail des tests) ou None."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT full_result FROM runs ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None
    return json.loads(row["full_result"])


def count_runs():
    """Retourne le nombre total de runs en base."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM runs")
    count = cursor.fetchone()[0]
    conn.close()
    return count