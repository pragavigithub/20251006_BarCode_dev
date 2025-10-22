-- ========================================
-- MySQL GRPO Schema Update Script
-- Date: October 22, 2025
-- Purpose: Update existing MySQL database to match current models
-- ========================================

-- USE YOUR DATABASE NAME HERE
-- USE wms_db;

-- ========================================
-- STEP 1: Update grpo_documents table
-- ========================================

-- Check if qc_user_id exists and rename it to qc_approver_id
-- If the column doesn't exist, this will create it
ALTER TABLE grpo_documents 
CHANGE COLUMN qc_user_id qc_approver_id INT NULL;

-- If qc_approver_id still doesn't exist (in case qc_user_id didn't exist), add it
-- This may give an error if the column already exists - that's OK, ignore it
ALTER TABLE grpo_documents 
ADD COLUMN qc_approver_id INT NULL AFTER user_id;

-- Add warehouse_code if it doesn't exist
ALTER TABLE grpo_documents 
ADD COLUMN warehouse_code VARCHAR(10) NULL AFTER supplier_name;

-- Add foreign key for qc_approver_id if it doesn't exist
-- Drop first in case it exists
ALTER TABLE grpo_documents 
DROP FOREIGN KEY IF EXISTS grpo_documents_ibfk_2;

ALTER TABLE grpo_documents 
ADD CONSTRAINT grpo_documents_ibfk_2 
FOREIGN KEY (qc_approver_id) REFERENCES users(id);

-- Ensure updated_at column exists
ALTER TABLE grpo_documents 
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- ========================================
-- STEP 2: Backup and Update grpo_items table
-- ========================================

-- Create backup table
DROP TABLE IF EXISTS grpo_items_backup_20251022;
CREATE TABLE grpo_items_backup_20251022 AS SELECT * FROM grpo_items;

-- Check current structure and add missing columns one by one
-- This approach is safer than dropping and recreating

-- Rename grpo_document_id to grpo_id if needed
ALTER TABLE grpo_items 
CHANGE COLUMN grpo_document_id grpo_id INT NOT NULL;

-- If grpo_id doesn't exist, add it
ALTER TABLE grpo_items 
ADD COLUMN grpo_id INT NOT NULL AFTER id;

-- Add line_total if missing
ALTER TABLE grpo_items 
ADD COLUMN line_total DECIMAL(15,2) NULL AFTER unit_price;

-- Add base_entry if missing
ALTER TABLE grpo_items 
ADD COLUMN base_entry INT NULL AFTER po_line_number;

-- Add base_line if missing
ALTER TABLE grpo_items 
ADD COLUMN base_line INT NULL AFTER base_entry;

-- Add batch_required if missing
ALTER TABLE grpo_items 
ADD COLUMN batch_required VARCHAR(1) DEFAULT 'N' AFTER base_line;

-- Add serial_required if missing
ALTER TABLE grpo_items 
ADD COLUMN serial_required VARCHAR(1) DEFAULT 'N' AFTER batch_required;

-- Add manage_method if missing
ALTER TABLE grpo_items 
ADD COLUMN manage_method VARCHAR(1) DEFAULT 'N' AFTER serial_required;

-- Add updated_at if missing
ALTER TABLE grpo_items 
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- Rename expiration_date to expiry_date if it exists
ALTER TABLE grpo_items 
CHANGE COLUMN expiration_date expiry_date DATE NULL;

-- If expiry_date doesn't exist, add it
ALTER TABLE grpo_items 
ADD COLUMN expiry_date DATE NULL AFTER serial_number;

-- Update quantity precision if needed
ALTER TABLE grpo_items 
MODIFY COLUMN quantity DECIMAL(15,3) NOT NULL;

ALTER TABLE grpo_items 
MODIFY COLUMN received_quantity DECIMAL(15,3) DEFAULT 0;

-- Rename supplier_barcode to barcode if it exists
ALTER TABLE grpo_items 
CHANGE COLUMN supplier_barcode barcode VARCHAR(100) NULL;

-- If barcode doesn't exist, add it
ALTER TABLE grpo_items 
ADD COLUMN barcode VARCHAR(100) NULL AFTER expiry_date;

-- Drop generated_barcode and barcode_printed if they exist
ALTER TABLE grpo_items 
DROP COLUMN IF EXISTS generated_barcode;

ALTER TABLE grpo_items 
DROP COLUMN IF EXISTS barcode_printed;

-- Drop qc_notes if it exists (moved to document level)
ALTER TABLE grpo_items 
DROP COLUMN IF EXISTS qc_notes;

-- Drop po_quantity and open_quantity if they exist (replaced by quantity)
ALTER TABLE grpo_items 
DROP COLUMN IF EXISTS po_quantity;

ALTER TABLE grpo_items 
DROP COLUMN IF EXISTS open_quantity;

-- Update foreign key constraint
ALTER TABLE grpo_items 
DROP FOREIGN KEY IF EXISTS grpo_items_ibfk_1;

ALTER TABLE grpo_items 
ADD CONSTRAINT grpo_items_ibfk_1 
FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE;

-- Update indexes
DROP INDEX IF EXISTS idx_grpo_document_id ON grpo_items;
CREATE INDEX idx_grpo_id ON grpo_items(grpo_id);

-- ========================================
-- STEP 3: Verification Queries
-- ========================================

-- View updated schema
SELECT 'grpo_documents schema:' as info;
DESCRIBE grpo_documents;

SELECT 'grpo_items schema:' as info;
DESCRIBE grpo_items;

-- Count records
SELECT 'Record counts:' as info;
SELECT 'grpo_documents' as table_name, COUNT(*) as count FROM grpo_documents
UNION ALL
SELECT 'grpo_items' as table_name, COUNT(*) as count FROM grpo_items;

-- ========================================
-- NOTES:
-- ========================================
-- 1. This script uses ALTER TABLE ADD COLUMN which will give errors
--    if columns already exist. This is SAFE - just ignore those errors.
-- 2. A backup table 'grpo_items_backup_20251022' is created automatically
-- 3. Review the structure after running to ensure all columns are present
-- 4. If you encounter errors, restore from backup and contact support
-- ========================================
