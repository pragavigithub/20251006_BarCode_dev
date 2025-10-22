# GRPO Module Migration Fix - October 22, 2025

## Issues Fixed

### 1. Import Error: `GRPODocument` Not Defined ✅
**Problem**: The error `name 'GRPODocument' is not defined` occurred when accessing dashboard and GRPO pages.

**Root Cause**: GRPO models were moved to `modules/grpo/models.py` but were not imported in the main `routes.py` file.

**Solution**: 
- Added import statement in `routes.py` line 15:
  ```python
  from modules.grpo.models import GRPODocument, GRPOItem, GRPOSerialNumber, GRPOBatchNumber, PurchaseDeliveryNote
  ```

**Status**: ✅ FIXED - Application running without import errors in Replit

---

### 2. MySQL Schema Mismatch ✅
**Problem**: MySQL database error when creating GRPO:
```
pymysql.err.OperationalError: (1054, "Unknown column 'grpo_documents.warehouse_code' in 'field list'")
```

**Root Cause**: MySQL database schema was outdated and missing columns added to the PostgreSQL models.

**Solution**: Updated `mysql_consolidated_migration.py` with correct schema:

#### Changes to `grpo_documents` table:
- ✅ Added `warehouse_code VARCHAR(10)` column
- ✅ Renamed `qc_user_id` to `qc_approver_id` for consistency
- ✅ Updated column order to match model definition

#### Changes to `grpo_items` table:
- ✅ Changed foreign key from `grpo_document_id` to `grpo_id`
- ✅ Added `line_total DECIMAL(15,2)` column
- ✅ Added `base_entry INT` column (SAP PO DocEntry)
- ✅ Added `base_line INT` column (SAP PO Line Number)
- ✅ Added `batch_required VARCHAR(1)` column
- ✅ Added `serial_required VARCHAR(1)` column
- ✅ Added `manage_method VARCHAR(1)` column
- ✅ Added `updated_at TIMESTAMP` column
- ✅ Renamed `expiration_date` to `expiry_date` (DATE type)
- ✅ Updated field types to match PostgreSQL models

**Status**: ✅ SCHEMA UPDATED - Migration script ready

---

## Action Required: Update Your MySQL Database

### Step 1: Backup Your Current MySQL Database
```bash
mysqldump -u your_username -p wms_db > wms_db_backup_$(date +%Y%m%d).sql
```

### Step 2: Run the Updated Migration Script

**Option A: Fresh Database (Recommended if testing)**
```bash
# Drop existing database and recreate
mysql -u root -p
DROP DATABASE wms_db;
CREATE DATABASE wms_db;
exit

# Run migration
python mysql_consolidated_migration.py
```

**Option B: Update Existing Database**
If you have existing data and want to preserve it, run this SQL manually:

```sql
-- Connect to your MySQL database
USE wms_db;

-- Add missing column to grpo_documents
ALTER TABLE grpo_documents 
ADD COLUMN warehouse_code VARCHAR(10) AFTER supplier_name;

-- Rename qc_user_id to qc_approver_id for consistency
ALTER TABLE grpo_documents 
CHANGE COLUMN qc_user_id qc_approver_id INT;

-- Update grpo_items table
-- WARNING: This will drop and recreate the table
-- Make sure to backup your data first!

-- Backup existing data
CREATE TABLE grpo_items_backup AS SELECT * FROM grpo_items;

-- Drop and recreate with new schema
DROP TABLE IF EXISTS grpo_items;

CREATE TABLE grpo_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grpo_id INT NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    item_name VARCHAR(200),
    quantity DECIMAL(15,3) NOT NULL,
    received_quantity DECIMAL(15,3) DEFAULT 0,
    unit_price DECIMAL(15,4),
    line_total DECIMAL(15,2),
    unit_of_measure VARCHAR(10),
    warehouse_code VARCHAR(10),
    bin_location VARCHAR(200),
    batch_number VARCHAR(50),
    serial_number VARCHAR(50),
    expiry_date DATE,
    barcode VARCHAR(100),
    qc_status VARCHAR(20) DEFAULT 'pending',
    po_line_number INT,
    base_entry INT,
    base_line INT,
    batch_required VARCHAR(1) DEFAULT 'N',
    serial_required VARCHAR(1) DEFAULT 'N',
    manage_method VARCHAR(1) DEFAULT 'N',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE,
    INDEX idx_grpo_id (grpo_id),
    INDEX idx_item_code (item_code),
    INDEX idx_qc_status (qc_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Restore data (map old column names to new ones)
INSERT INTO grpo_items (
    id, grpo_id, item_code, item_name, quantity, received_quantity,
    unit_price, unit_of_measure, warehouse_code, bin_location,
    batch_number, serial_number, expiry_date, barcode, qc_status,
    po_line_number, created_at
)
SELECT 
    id, grpo_document_id, item_code, item_name, po_quantity, received_quantity,
    unit_price, unit_of_measure, warehouse_code, bin_location,
    batch_number, serial_number, expiration_date, supplier_barcode, qc_status,
    po_line_number, created_at
FROM grpo_items_backup;

-- Drop backup table after verification
-- DROP TABLE grpo_items_backup;
```

### Step 3: Verify the Migration

1. **Check table structure**:
   ```sql
   DESCRIBE grpo_documents;
   DESCRIBE grpo_items;
   ```

2. **Test GRPO creation**: Try creating a new GRPO document through the application

3. **Verify data**: Ensure all existing GRPO data is intact

---

## Summary of Changes

### Files Modified:
1. ✅ `routes.py` - Added GRPO model imports
2. ✅ `mysql_consolidated_migration.py` - Updated GRPO table schemas
3. ✅ `REPLIT_POSTGRESQL_MIGRATION_STATUS.md` - Documented changes

### Replit Environment:
- ✅ Application running successfully
- ✅ PostgreSQL database with correct schema
- ✅ No import errors
- ✅ GRPO module functional

### Local/MySQL Environment:
- ⚠️ **Action Required**: Update MySQL database schema
- 📋 Migration script updated and ready
- 💾 Backup recommended before migration

---

## Testing Checklist

After updating MySQL:
- [ ] Can access dashboard without errors
- [ ] Can access GRPO list page
- [ ] Can create new GRPO document
- [ ] Can add items to GRPO
- [ ] Can save and submit GRPO
- [ ] Can view GRPO details
- [ ] Serial number management works
- [ ] Batch number management works

---

## Support

If you encounter any issues during migration:
1. Check the backup you created in Step 1
2. Review the error logs
3. Verify MySQL version compatibility (MySQL 5.7+ or 8.0+ recommended)
4. Ensure user has ALTER TABLE privileges

---

**Migration Status**: Ready for deployment
**Last Updated**: October 22, 2025
**Tested On**: Replit (PostgreSQL) - ✅ WORKING
