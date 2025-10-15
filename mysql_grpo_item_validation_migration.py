#!/usr/bin/env python3
"""
MySQL Migration Script - Add Item Validation Fields to GRPO Module
Date: October 15, 2025

CHANGES:
✅ Add batch_required column to grpo_items table
✅ Add serial_required column to grpo_items table
✅ Add manage_method column to grpo_items table
"""

import os
import sys
import logging
import pymysql
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GRPOItemValidationMigration:
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
    
    def add_validation_columns(self):
        """Add validation columns to grpo_items table"""
        try:
            logger.info("🔄 Adding item validation columns to grpo_items table...")
            
            # Add batch_required column if it doesn't exist
            if not self.column_exists('grpo_items', 'batch_required'):
                self.cursor.execute("""
                    ALTER TABLE grpo_items 
                    ADD COLUMN batch_required VARCHAR(1) DEFAULT 'N' AFTER base_line
                """)
                logger.info("✅ Added batch_required column to grpo_items")
            else:
                logger.info("ℹ️ batch_required column already exists in grpo_items")
            
            # Add serial_required column if it doesn't exist
            if not self.column_exists('grpo_items', 'serial_required'):
                self.cursor.execute("""
                    ALTER TABLE grpo_items 
                    ADD COLUMN serial_required VARCHAR(1) DEFAULT 'N' AFTER batch_required
                """)
                logger.info("✅ Added serial_required column to grpo_items")
            else:
                logger.info("ℹ️ serial_required column already exists in grpo_items")
            
            # Add manage_method column if it doesn't exist
            if not self.column_exists('grpo_items', 'manage_method'):
                self.cursor.execute("""
                    ALTER TABLE grpo_items 
                    ADD COLUMN manage_method VARCHAR(1) DEFAULT 'N' COMMENT 'A=Average, R=FIFO/Release, N=None' AFTER serial_required
                """)
                logger.info("✅ Added manage_method column to grpo_items")
            else:
                logger.info("ℹ️ manage_method column already exists in grpo_items")
            
            self.connection.commit()
            logger.info("✅ GRPO item validation migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding validation columns: {e}")
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
    logger.info("GRPO Item Validation Migration Script")
    logger.info("=" * 80)
    
    migration = GRPOItemValidationMigration()
    
    try:
        config = migration.get_database_config()
        
        if not migration.connect(config):
            logger.error("Failed to connect to database. Exiting...")
            return False
        
        success = migration.add_validation_columns()
        
        if success:
            logger.info("=" * 80)
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info("New columns added to grpo_items:")
            logger.info("  - batch_required VARCHAR(1) DEFAULT 'N'")
            logger.info("  - serial_required VARCHAR(1) DEFAULT 'N'")
            logger.info("  - manage_method VARCHAR(1) DEFAULT 'N' (A=Average, R=FIFO/Release, N=None)")
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
