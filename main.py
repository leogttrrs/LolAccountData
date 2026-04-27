from datetime import datetime, timezone
from ETLs.extract import run_extract
from ETLs.transform import run_transform
from ETLs.load import run_load, log_pipeline_run

def main():
    started_at = datetime.now(timezone.utc)
    print(f"[main] Pipeline started at {started_at.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

    try:
        puuid, matches = run_extract()

        df = run_transform(puuid, matches)
        rows_inserted = run_load(df)

        log_pipeline_run(
            started_at=started_at,
            matches_processed=len(matches),
            rows_inserted=rows_inserted,
            status="SUCCESS",
        )

        print(f"\n[main] Pipeline finished successfully. {rows_inserted} new rows inserted.")

    except Exception as e:
        log_pipeline_run(
            started_at=started_at,
            matches_processed=0,
            rows_inserted=0,
            status="FAILED",
            error_message=str(e),
        )

        print(f"\n[main] Pipeline FAILED: {e}")
        raise

if __name__ == "__main__":
    main()
