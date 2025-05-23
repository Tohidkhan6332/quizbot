from __future__ import annotations
import logging
from typing import Optional
from bot.database import Database

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migrations.log')
    ]
)
logger = logging.getLogger(__name__)

class MigrationError(Exception):
    """Custom exception for migration failures."""
    pass

def run_migrations() -> bool:
    """
    Run initial database migrations.
    
    Returns:
        bool: True if migrations succeeded, False otherwise
    """
    try:
        logger.info("Starting database migrations")
        
        # Initialize database connection with context manager if available
        if hasattr(Database, '__enter__'):
            with Database() as db:
                logger.info("Database connection established")
                _perform_migrations(db)
        else:
            logger.info("Database connection established")
            Database.initialize()
            _perform_migrations(Database)
        
        logger.info("Migrations completed successfully")
        return True
        
    except MigrationError as e:
        logger.error(f"Migration failed: {e}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error during migration: {e}", exc_info=True)
        return False
    finally:
        # Cleanup resources
        if hasattr(Database, 'close'):
            Database.close()
            logger.info("Database connection closed")

def _perform_migrations(db: Database) -> None:
    """Perform the actual migration steps."""
    try:
        db.create_tables()
        logger.info("Tables created successfully")
        
        # Add additional migration steps here if needed
        # Example: db.add_indexes(), db.populate_initial_data(), etc.
        
    except Exception as e:
        logger.error(f"Migration step failed: {e}")
        raise MigrationError("Failed to execute migration steps") from e

if __name__ == '__main__':
    if not run_migrations():
        exit(1)
