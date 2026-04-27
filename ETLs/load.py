import os
import uuid
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def _ensure_tables() -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS match_history (
                match_id VARCHAR PRIMARY KEY,
                queue_type VARCHAR,
                champion_name VARCHAR,
                kills INTEGER,
                deaths INTEGER,
                assists INTEGER,
                kda_score FLOAT,
                damage_dealt INTEGER,
                vision_score INTEGER,
                cs_per_min FLOAT,
                game_duration_min FLOAT,
                win BOOLEAN,
                placement INTEGER,
                performance_flag VARCHAR,
                played_at TIMESTAMP,
                patch VARCHAR
            )
        """))

        conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS pipeline_runs (
                        run_id              VARCHAR PRIMARY KEY,
                        started_at          TIMESTAMP,
                        finished_at         TIMESTAMP,
                        matches_processed   INTEGER,
                        rows_inserted       INTEGER,
                        status              VARCHAR,
                        error_message       TEXT
                    )
                """))

    print("[load] Tablse verified.")

def load_match_history(df: pd.DataFrame) -> int:
    rows_before = _count_rows("match_history")

    df.to_sql(
        name="match_history",
        con=engine,
        if_exists="append",
        index=False,
        method=_upsert_on_conflict,
    )

    rows_after  = _count_rows("match_history")
    rows_inserted = rows_after - rows_before

    print(f"[load] match_history → {rows_inserted} new rows inserted ({rows_after} total).")
    return rows_inserted

def _upsert_on_conflict(table, conn, keys, data_iter):
    rows = [dict(zip(keys, row)) for row in data_iter]

    stmt = text(f"""
        INSERT INTO {table.name} ({", ".join(keys)})
        VALUES ({", ".join([f":{k}" for k in keys])})
        ON CONFLICT (match_id) DO NOTHING
    """)

    conn.execute(stmt, rows)

def run_load(df: pd.DataFrame) -> int:
    print("[load] Starting load phase...")
    _ensure_tables()
    rows_inserted = load_match_history(df)
    return rows_inserted

def _count_rows(table_name: str) -> int:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()

def log_pipeline_run(
            started_at: datetime,
            matches_processed: int,
            rows_inserted: int,
            status: str,
            error_message: str = None,
        ) -> None:

    run = pd.DataFrame([{
        "run_id": str(uuid.uuid4()),
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc),
        "matches_processed": matches_processed,
        "rows_inserted": rows_inserted,
        "status": status,
        "error_message": error_message,
    }])

    run.to_sql(
        name="pipeline_runs",
        con=engine,
        if_exists="append",
        index=False,
    )

    print(f"[load] pipeline_runs → run logged as {status}.")

if __name__ == "__main__":
    from extract import run_extract
    from transform import run_transform

    puuid, matches = run_extract()
    df = run_transform(puuid, matches)
    rows_inserted  = run_load(df)

    print(f"\n[load] Done. {rows_inserted} new rows inserted.")
