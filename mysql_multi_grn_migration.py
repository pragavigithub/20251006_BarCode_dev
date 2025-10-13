#!/usr/bin/env python3
"""
MySQL Migration Script for Multiple GRN Creation Module
Adds tables for batch GRN creation from multiple Purchase Orders

NEW TABLES:
✅ multi_grn_batches - Main batch records for multiple GRN creation
✅ multi_grn_po_links - Links between batches and selected Purchase Orders
✅ multi_grn_line_selections - Selected line items from Purchase Orders

Date: October 13, 2025
"""

import os
import sys
import logging
import pymysql
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiGRNMySQLMigration:
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
    
    def create_multi_grn_tables(self):
        """Create tables for Multiple GRN Creation module"""
        
        tables = {
            # 1. Multi GRN Batches - Main batch records
            'multi_grn_batches': '''
                CREATE TABLE IF NOT EXISTS multi_grn_batches (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    customer_code VARCHAR(50) NOT NULL,
                    customer_name VARCHAR(200) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'draft',
                    total_pos INT DEFAULT 0,
                    total_grns_created INT DEFAULT 0,
                    sap_session_metadata TEXT,
                    error_log TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    posted_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_customer_code (customer_code),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 2. Multi GRN PO Links - Links between batches and POs
            'multi_grn_po_links': '''
                CREATE TABLE IF NOT EXISTS multi_grn_po_links (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    batch_id INT NOT NULL,
                    po_doc_entry INT NOT NULL,
                    po_doc_num VARCHAR(50) NOT NULL,
                    po_card_code VARCHAR(50),
                    po_card_name VARCHAR(200),
                    po_doc_date DATE,
                    po_doc_total DECIMAL(15,2),
                    status VARCHAR(20) NOT NULL DEFAULT 'selected',
                    sap_grn_doc_num VARCHAR(50),
                    sap_grn_doc_entry INT,
                    posted_at TIMESTAMP NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (batch_id) REFERENCES multi_grn_batches(id) ON DELETE CASCADE,
                    UNIQUE KEY uq_batch_po (batch_id, po_doc_entry),
                    INDEX idx_batch_id (batch_id),
                    INDEX idx_po_doc_entry (po_doc_entry),
                    INDEX idx_po_doc_num (po_doc_num),
                    INDEX idx_status (status),
                    INDEX idx_sap_grn_doc_num (sap_grn_doc_num)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 3. Multi GRN Line Selections - Selected line items
            'multi_grn_line_selections': '''
                CREATE TABLE IF NOT EXISTS multi_grn_line_selections (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    po_link_id INT NOT NULL,
                    po_line_num INT NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_description VARCHAR(200),
                    ordered_quantity DECIMAL(15,3) NOT NULL,
                    open_quantity DECIMAL(15,3) NOT NULL,
                    selected_quantity DECIMAL(15,3) NOT NULL,
                    warehouse_code VARCHAR(50),
                    bin_location VARCHAR(200),
                    unit_price DECIMAL(15,4),
                    line_status VARCHAR(20),
                    inventory_type VARCHAR(20),
                    posting_payload TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (po_link_id) REFERENCES multi_grn_po_links(id) ON DELETE CASCADE,
                    INDEX idx_po_link_id (po_link_id),
                    INDEX idx_item_code (item_code),
                    INDEX idx_po_line_num (po_line_num)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        }
        
        try:
            for table_name, create_sql in tables.items():
                logger.info(f"Creating table: {table_name}")
                self.cursor.execute(create_sql)
                logger.info(f"✅ Table {table_name} created successfully")
            
            self.connection.commit()
            logger.info("✅ All Multi GRN tables created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            self.connection.rollback()
            return False
    
    def update_user_permissions(self):
        """Add multiple_grn permission to existing users"""
        try:
            logger.info("Updating user permissions to include multiple_grn module...")
            
            # Get all users
            self.cursor.execute("SELECT id, role, permissions FROM users")
            users = self.cursor.fetchall()
            
            import json
            updated = 0
            
            for user_id, role, permissions_json in users:
                # Parse existing permissions or create new
                if permissions_json:
                    try:
                        permissions = json.loads(permissions_json)
                    except:
                        permissions = {}
                else:
                    permissions = {}
                
                # Add multiple_grn permission based on role
                if 'multiple_grn' not in permissions:
                    if role in ['admin', 'manager', 'user']:
                        permissions['multiple_grn'] = True
                    else:
                        permissions['multiple_grn'] = False
                    
                    # Update user permissions
                    self.cursor.execute(
                        "UPDATE users SET permissions = %s WHERE id = %s",
                        (json.dumps(permissions), user_id)
                    )
                    updated += 1
            
            self.connection.commit()
            logger.info(f"✅ Updated permissions for {updated} users")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating permissions: {e}")
            self.connection.rollback()
            return False
    
    def verify_migration(self):
        """Verify that all tables were created successfully"""
        try:
            logger.info("\n🔍 Verifying migration...")
            
            tables_to_check = [
                'multi_grn_batches',
                'multi_grn_po_links',
                'multi_grn_line_selections'
            ]
            
            for table in tables_to_check:
                self.cursor.execute(f"SHOW TABLES LIKE '{table}'")
                result = self.cursor.fetchone()
                if result:
                    self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = self.cursor.fetchone()[0]
                    logger.info(f"✅ {table}: exists (rows: {count})")
                else:
                    logger.error(f"❌ {table}: NOT FOUND")
                    return False
            
            logger.info("\n✅ Migration verification completed successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Verification error: {e}")
            return False
    
    def run_migration(self):
        """Run the complete migration"""
        logger.info("=" * 60)
        logger.info("MULTIPLE GRN CREATION MODULE - MySQL Migration")
        logger.info("=" * 60)
        
        # Get database config and connect
        config = self.get_database_config()
        
        if not self.connect(config):
            logger.error("Failed to connect to database. Exiting.")
            return False
        
        # Create tables
        logger.info("\n📦 Creating Multi GRN tables...")
        if not self.create_multi_grn_tables():
            return False
        
        # Update permissions
        logger.info("\n🔐 Updating user permissions...")
        if not self.update_user_permissions():
            logger.warning("⚠️ Failed to update permissions, but continuing...")
        
        # Verify migration
        if not self.verify_migration():
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info("\nNew tables created:")
        logger.info("  - multi_grn_batches")
        logger.info("  - multi_grn_po_links")
        logger.info("  - multi_grn_line_selections")
        logger.info("\nModule ready: /multi-grn/")
        logger.info("=" * 60)
        
        return True
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("✅ Database connection closed")

def main():
    migration = MultiGRNMySQLMigration()
    try:
        success = migration.run_migration()
        sys.exit(0 if success else 1)
    finally:
        migration.close()

if __name__ == '__main__':
    main()
