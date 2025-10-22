-- =====================================================
-- GRPO Batch/Serial Conditional Display Enhancement
-- Date: 2025-10-22
-- Description: Implement conditional display of batch/serial fields based on SAP item validation
-- =====================================================

-- The required database fields are already part of the grpo_items table schema
-- This migration documents the enhancement for conditional field display

-- Verify required columns exist in grpo_items table
-- Expected schema additions for item management tracking:
-- - batch_required VARCHAR(1) DEFAULT 'N'  -- 'Y' or 'N' - indicates if batch management is required
-- - serial_required VARCHAR(1) DEFAULT 'N' -- 'Y' or 'N' - indicates if serial management is required
-- - manage_method VARCHAR(1) DEFAULT 'N'   -- 'A' (Average), 'R' (FIFO/Release), 'N' (None)

-- Check if batch_required column exists, add if missing
SET @dbname = DATABASE();
SET @tablename = 'grpo_items';
SET @columnname = 'batch_required';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(1) DEFAULT "N"')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Check if serial_required column exists, add if missing
SET @columnname = 'serial_required';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(1) DEFAULT "N"')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Check if manage_method column exists, add if missing
SET @columnname = 'manage_method';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(1) DEFAULT "N"')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Application Logic Changes (Frontend):
-- 1. Added wrapper div 'batch_section' around batch fields with id for show/hide control
-- 2. Enabled SAP validation in handleItemCodeChange() function
-- 3. Updated validateItemCodeFromSAP() to use batch_section and serial_section divs
-- 4. Implemented conditional display logic:
--    - If item is SERIAL managed: Show serial number fields, hide batch fields
--    - If item is BATCH managed: Show batch fields, hide serial number fields
--    - If item is NOT batch/serial managed: Hide both sections (standard item)

-- Application Logic Changes (Backend):
-- Routes already validate items via SAP Integration:
--   - modules/grpo/routes.py: add_grpo_item() calls sap.validate_item_code()
--   - sap_integration.py: validate_item_code() queries SAP B1 SQL 'ItemCode_Batch_Serial_Val'
--   - Returns: batch_required (bool), serial_required (bool), manage_method (str)

-- SAP Integration Details:
-- The system queries SAP B1 using SQL query 'ItemCode_Batch_Serial_Val'
-- Returns fields:
--   - BatchNum: 'Y' if batch managed, 'N' otherwise
--   - SerialNum: 'Y' if serial managed, 'N' otherwise  
--   - NonBatch_NonSerialMethod: 'A' (Average), 'R' (FIFO), 'N' (None)

-- Business Rules:
-- 1. An item can be either batch managed OR serial managed, not both
-- 2. Batch managed items require batch number and optionally expiry date
-- 3. Serial managed items require one serial number per unit quantity
-- 4. Standard items (non-batch, non-serial) don't show batch/serial fields

SELECT 'GRPO Batch/Serial Conditional Display Enhancement - Completed' AS status;
