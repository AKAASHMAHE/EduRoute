"""
Database Migration Runner for Train Booking Date Reminder System.
Ensures zero-downtime, non-destructive schema migrations for existing and fresh databases.
"""

import logging
from sqlalchemy import inspect, text
from app.models import db

logger = logging.getLogger(__name__)


def run_migrations(app):
    """
    Apply incremental migrations to SQLite database.
    Preserves all existing Journey records.
    """
    with app.app_context():
        # First ensure all base tables are registered
        db.create_all()

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "journeys" in existing_tables:
            columns = [col["name"] for col in inspector.get_columns("journeys")]

            # Check if holiday_id column is present
            if "holiday_id" not in columns:
                logger.info("Migrating schema: Adding holiday_id column to journeys table")
                with db.engine.connect() as conn:
                    conn.execute(
                        text("ALTER TABLE journeys ADD COLUMN holiday_id INTEGER REFERENCES holidays(id)")
                    )
                    conn.commit()
                logger.info("Successfully added holiday_id column to journeys table")

            # Check indexes
            indexes = [idx["name"] for idx in inspector.get_indexes("journeys")]
            if "ix_journeys_holiday_id" not in indexes:
                with db.engine.connect() as conn:
                    try:
                        conn.execute(
                            text("CREATE INDEX IF NOT EXISTS ix_journeys_holiday_id ON journeys (holiday_id)")
                        )
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Index creation note: {e}")

        logger.info("Database migration completed successfully.")


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    run_migrations(app)
    print("Database migration executed successfully.")
