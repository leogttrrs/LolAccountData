import logging
from datetime import datetime, timezone
from ETLs.extract import run_extract
from ETLs.transform import run_transform
from ETLs.load import run_load, log_pipeline_run

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

def main():
    started_at = datetime.now(timezone.utc)
    logging.info(f"Main: Pipeline started at {started_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")

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

        logging.info(f"Main: Pipeline finished successfully. {rows_inserted} new rows inserted.")

    except Exception as e:
        log_pipeline_run(
            started_at=started_at,
            matches_processed=0,
            rows_inserted=0,
            status="FAILED",
            error_message=str(e),
        )

        logging.error(f"Main: Pipeline FAILED: {e}")
        raise

if __name__ == "__main__":
    main()
