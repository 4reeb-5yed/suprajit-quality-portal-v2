import argparse
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from app.sync_engine import SyncEngine

# Setup basic logging for the ingestion job
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'ingestion.log'))
    ]
)
logger = logging.getLogger('ingest_batch')

def main():
    parser = argparse.ArgumentParser(description="Suprajit Quality Portal - Batch Ingestion")
    parser.add_argument('--date', type=str, help='Specific date to process in YYYY-MM-DD format (defaults to yesterday)')
    args = parser.parse_args()

    # Load environment variables (db path, storage base)
    load_dotenv()
    db_path = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), 'data', 'portal.db'))
    storage_base = os.getenv("STORAGE_FOLDER", os.path.join(os.path.dirname(__file__), 'storage'))
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    os.makedirs(storage_base, exist_ok=True)

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Must be YYYY-MM-DD.")
            return

    logger.info("==================================================")
    if target_date:
        logger.info(f"Starting batch ingestion for explicit date: {target_date}")
    else:
        logger.info("Starting N-1 batch ingestion (target: yesterday)")

    engine = SyncEngine(db_path=db_path, storage_base=storage_base)
    
    try:
        inserted = engine.run_batch(target_date)
        logger.info(f"Batch completed successfully. Inserted {inserted} new reports.")
    except Exception as e:
        logger.exception("CRITICAL ERROR during batch ingestion")

if __name__ == "__main__":
    main()
