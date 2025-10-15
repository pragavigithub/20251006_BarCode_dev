#!/usr/bin/env python3
"""
MySQL Migration: GRPO Serial and Batch Number Tables
Creates tables for storing serial and batch number details for GRPO items
Supports SAP B1 JSON format with detailed tracking

Tables Created:
- grpo_serial_numbers: Stores individual serial numbers with barcode
- grpo_batch_numbers: Stores batch numbers with quantities and barcodes

Run with: python mysql_grpo_serial_batch_migration.py
"""

import pymysql
import os
import sys
from datetime import datetime

def get_mysql_connection():
    """Get MySQL connection from environment variables"""
    try:
        # Parse MySQL URL format: mysql://user:password@host:port/database
        db_url = os.environ.get('MYSQL_URL', '')
        
        if not db_url:
            print("❌ MYSQL_URL environment variable not set")
            return None
            
        # Parse connection string
        if db_url.startswith('mysql://'):
            db_url = db_url[8:]  # Remove mysql://
            
        # Split user:pass@host:port/db
        if '@' in db_url:
            auth, location = db_url.split('@')
            user, password = auth.split(':') if ':' in auth else (auth, '')
            
            if '/' in location:
                host_port, database = location.split('/')
                host, port = host_port.split(':') if ':' in host_port else (host_port, '3306')
            else:
                host, port = location.split(':') if ':' in location else (location, '3306')
                database = 'warehouse_db'
        else:
            print("❌ Invalid MYSQL_URL format")
            return None
            
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✅ Connected to MySQL: {host}:{port}/{database}")
        return connection
        
    except Exception as e:
        print(f"❌ MySQL connection failed: {str(e)}")
        return None

def run_migration():
    """Run the migration"""
    connection = get_mysql_connection()
    
    if not connection:
        print("⚠️ Skipping MySQL migration - connection not available")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Check if grpo_serial_numbers table exists
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'grpo_serial_numbers'
        """)
        result = cursor.fetchone()
        serial_table_exists = result['count'] > 0
        
        # Check if grpo_batch_numbers table exists
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'grpo_batch_numbers'
        """)
        result = cursor.fetchone()
        batch_table_exists = result['count'] > 0
        
        # Create grpo_serial_numbers table if it doesn't exist
        if not serial_table_exists:
            print("📝 Creating grpo_serial_numbers table...")
            cursor.execute("""
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
            print("✅ grpo_serial_numbers table created successfully")
        else:
            print("ℹ️ grpo_serial_numbers table already exists")
        
        # Create grpo_batch_numbers table if it doesn't exist
        if not batch_table_exists:
            print("📝 Creating grpo_batch_numbers table...")
            cursor.execute("""
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
            print("✅ grpo_batch_numbers table created successfully")
        else:
            print("ℹ️ grpo_batch_numbers table already exists")
        
        # Commit the changes
        connection.commit()
        
        print("\n🎉 Migration completed successfully!")
        print("=" * 60)
        print("Tables created/verified:")
        print("  ✓ grpo_serial_numbers - Serial number tracking with barcodes")
        print("  ✓ grpo_batch_numbers - Batch number tracking with barcodes")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        connection.rollback()
        return False
        
    finally:
        cursor.close()
        connection.close()
        print("📤 Database connection closed")

if __name__ == "__main__":
    print("=" * 60)
    print("GRPO Serial/Batch Number Tables Migration")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration script completed successfully")
        sys.exit(0)
    else:
        print("\n⚠️ Migration had warnings or was skipped")
        sys.exit(1)
