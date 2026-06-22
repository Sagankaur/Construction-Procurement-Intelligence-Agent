import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DB_NAME = "site_sage.db"


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_db_path() -> Path:
    return (Path(__file__).parent / DB_NAME).resolve()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            content TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            chunk_idx INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_name TEXT NOT NULL,
            vendor_name TEXT NOT NULL,
            order_date TEXT,
            promised_delivery_date TEXT,
            expected_roj_date TEXT,
            delay_risk TEXT NOT NULL,
            risk_score REAL,
            expected_delay_days REAL,
            recommendation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _ensure_prediction_columns(conn)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS procurement_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            field_value TEXT NOT NULL,
            confidence TEXT DEFAULT 'medium',
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def _ensure_prediction_columns(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(predictions)").fetchall()
    }
    additions = {
        "expected_roj_date": "TEXT",
        "risk_score": "REAL",
        "recommendation": "TEXT",
    }
    for column, column_type in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE predictions ADD COLUMN {column} {column_type}")


def list_documents(db_path: Optional[Path] = None) -> list[sqlite3.Row]:
    init_db(db_path)
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT
            d.id,
            d.filename,
            d.uploaded_at,
            COUNT(c.id) AS chunk_count
        FROM documents d
        LEFT JOIN document_chunks c ON c.doc_id = d.id
        GROUP BY d.id
        ORDER BY d.uploaded_at DESC
        """
    ).fetchall()
    conn.close()
    return rows


def count_rows(table_name: str, db_path: Optional[Path] = None) -> int:
    if table_name not in {"documents", "document_chunks", "predictions"}:
        raise ValueError(f"Unsupported table: {table_name}")
    init_db(db_path)
    conn = get_connection(db_path)
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    conn.close()
    return int(count)


def save_prediction(prediction: Dict[str, Any], db_path: Optional[Path] = None) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute(
        """
        INSERT INTO predictions (
            material_name,
            vendor_name,
            order_date,
            promised_delivery_date,
            expected_roj_date,
            delay_risk,
            risk_score,
            expected_delay_days,
            recommendation
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prediction.get("material_name", ""),
            prediction.get("vendor_name", ""),
            prediction.get("order_date", ""),
            prediction.get("promised_delivery_date", ""),
            prediction.get("expected_roj_date", ""),
            prediction.get("risk_level", ""),
            prediction.get("risk_score", 0),
            prediction.get("expected_delay_days", 0),
            prediction.get("recommendation", ""),
        ),
    )
    conn.commit()
    conn.close()


def seed_rows(rows: Iterable[Dict[str, Any]], db_path: Optional[Path] = None) -> None:
    for row in rows:
        save_prediction(row, db_path)


def save_procurement_facts(
    doc_id: int,
    facts: List[Dict[str, str]],
    db_path: Optional[Path] = None,
) -> None:
    """Save extracted procurement facts for a document."""
    init_db(db_path)
    conn = get_connection(db_path)
    conn.executemany(
        """
        INSERT INTO procurement_facts (doc_id, field_name, field_value, confidence)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                doc_id,
                fact.get("field", ""),
                fact.get("value", ""),
                fact.get("confidence", "medium"),
            )
            for fact in facts
        ],
    )
    conn.commit()
    conn.close()


def get_procurement_facts(
    doc_id: Optional[int] = None, db_path: Optional[Path] = None
) -> list[sqlite3.Row]:
    """Retrieve procurement facts, optionally filtered by document."""
    init_db(db_path)
    conn = get_connection(db_path)
    if doc_id is not None:
        rows = conn.execute(
            """
            SELECT pf.id, pf.doc_id, d.filename, pf.field_name, pf.field_value,
                   pf.confidence, pf.extracted_at
            FROM procurement_facts pf
            JOIN documents d ON d.id = pf.doc_id
            WHERE pf.doc_id = ?
            ORDER BY pf.id
            """,
            (doc_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT pf.id, pf.doc_id, d.filename, pf.field_name, pf.field_value,
                   pf.confidence, pf.extracted_at
            FROM procurement_facts pf
            JOIN documents d ON d.id = pf.doc_id
            ORDER BY pf.extracted_at DESC
            """
        ).fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print(f"Initialized DB at {get_db_path()}")
