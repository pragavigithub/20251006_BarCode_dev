#!/usr/bin/env python3
"""
MySQL Migration Script - Add PO Series and DocEntry to GRPO Module
Date: October 2025

CHANGES:
✅ Add po_series column to grpo_documents table
✅ Add po_doc_entry column to grpo_documents table
"""

import os
import sys
import logging
import pymysql
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GRPOSeriesMigration:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_database_config(self):
        """Get database configuration from environment or user input"""
        config = {
            'host': os.getenv('MYSQL_HOST') or input('MySQL Host (localhost): ') or 'localhost',
            'port': int(os.getenv('MYSQL_PORT') or input('MySQL Port (3306): ') or '3306'),
            'user': os.getenv('MYSQL_USER') or input('MySQL User (root): ') or 'root',
            'password': os.getenv('MYSQL_PASSWORD') or input('MySQL Password: '),
            'database': os.getenv('MYSQL_DATABASE') or input('Database Name (wms_db_dev): ') or 'wms_db_dev',
            'charset': 'utf8mb4',
            'autocommit': False
        }
        return config

    def connect(self, config):
        """Connect to MySQL database"""
        try:
            self.connection = pymysql.connect(**config)
            self.cursor = self.connection.cursor()
            logger.info(f"✅ Connected to MySQL: {config['database']}")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        try:
            self.cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}' 
                AND COLUMN_NAME = '{column_name}'
            """)
            result = self.cursor.fetchone()
            return result[0] > 0
        except Exception as e:
            logger.error(f"Error checking column existence: {e}")
            return False

    def table_exists(self, table_name):
        """Check if a table exists in the database"""
        try:
            self.cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table_name}'
            """)
            result = self.cursor.fetchone()
            return result[0] > 0
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False

    def create_tables(self):
        """Create grpo_serial_numbers and grpo_batch_numbers tables if they don't exist"""
        # Check and create grpo_serial_numbers table
        if not self.table_exists('grpo_serial_numbers'):
            logger.info("📝 Creating grpo_serial_numbers table...")
            self.cursor.execute("""
                CREATE TABLE grpo_serial_numbers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    grpo_item_id INT NOT NULL,
                    manufacturer_serial_number VARCHAR(100),
                    internal_serial_number VARCHAR(100) NOT NULL UNIQUE,
                    expiry_date DATE,
                    manufacture_date DATE,
                    notes TEXT,
                    barcode VARCHAR(200),
                    quantity DECIMAL(15,3) DEFAULT 1.0,
                    base_line_number INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (grpo_item_id) REFERENCES grpo_items(id) ON DELETE CASCADE,
                    INDEX idx_grpo_item_id (grpo_item_id),
                    INDEX idx_internal_serial (internal_serial_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            logger.info("✅ grpo_serial_numbers table created successfully")
        else:
            logger.info("ℹ️ grpo_serial_numbers table already exists")

        # Check and create grpo_batch_numbers table
        if not self.table_exists('grpo_batch_numbers'):
            logger.info("📝 Creating grpo_batch_numbers table...")
            self.cursor.execute("""
                CREATE TABLE grpo_batch_numbers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    grpo_item_id INT NOT NULL,
                    batch_number VARCHAR(100) NOT NULL,
                    quantity DECIMAL(15,3) NOT NULL,
                    base_line_number INT DEFAULT 0,
                    manufacturer_serial_number VARCHAR(100),
                    internal_serial_number VARCHAR(100),
                    expiry_date DATE,
                    barcode VARCHAR(200),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (grpo_item_id) REFERENCES grpo_items(id) ON DELETE CASCADE,
                    INDEX idx_grpo_item_id (grpo_item_id),
                    INDEX idx_batch_number (batch_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            logger.info("✅ grpo_batch_numbers table created successfully")
        else:
            logger.info("ℹ️ grpo_batch_numbers table already exists")

    def add_grpo_series_columns(self):
        """Add po_series and po_doc_entry columns to grpo_documents table"""
        try:
            logger.info("🔄 Adding PO series and DocEntry columns to grpo_documents table...")

            # Add po_series column if it doesn't exist
            if not self.column_exists('grpo_documents', 'po_series'):
                self.cursor.execute("""
                    ALTER TABLE grpo_documents 
                    ADD COLUMN po_series VARCHAR(20) NULL AFTER po_number
                """)
                logger.info("✅ Added po_series column to grpo_documents")
            else:
                logger.info("ℹ️ po_series column already exists in grpo_documents")

            # Add po_doc_entry column if it doesn't exist
            if not self.column_exists('grpo_documents', 'po_doc_entry'):
                self.cursor.execute("""
                    ALTER TABLE grpo_documents 
                    ADD COLUMN po_doc_entry INT NULL AFTER po_series
                """)
                logger.info("✅ Added po_doc_entry column to grpo_documents")
            else:
                logger.info("ℹ️ po_doc_entry column already exists in grpo_documents")

            # Add index on po_doc_entry for better query performance
            try:
                self.cursor.execute("""
                    CREATE INDEX idx_po_doc_entry ON grpo_documents(po_doc_entry)
                """)
                logger.info("✅ Added index on po_doc_entry")
            except pymysql.err.OperationalError as e:
                if "Duplicate key name" in str(e):
                    logger.info("ℹ️ Index on po_doc_entry already exists")
                else:
                    raise

            self.connection.commit()
            logger.info("✅ GRPO series migration completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error adding GRPO series columns: {e}")
            self.connection.rollback()
            return False

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("🔌 Database connection closed")

def main():
    """Main migration execution"""
    logger.info("=" * 80)
    logger.info("GRPO Series and DocEntry Migration Script")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    migration = GRPOSeriesMigration()

    try:
        config = migration.get_database_config()

        if not migration.connect(config):
            logger.error("Failed to connect to database. Exiting...")
            return False

        # Create tables if they don't exist
        migration.create_tables()

        # Add columns to grpo_documents
        success = migration.add_grpo_series_columns()

        if success:
            logger.info("=" * 80)
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)
            logger.info("New columns added to grpo_documents:")
            logger.info("  - po_series VARCHAR(20) NULL")
            logger.info("  - po_doc_entry INT NULL")
            logger.info("=" * 80)
        else:
            logger.error("Migration failed. Please check the errors above.")
            return False

    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        return False
    finally:
        migration.close()

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)