# MySQL GRPO Missing Fields - Complete Fix Guide
**Date**: October 22, 2025  
**Status**: ⚠️ CRITICAL - Your MySQL database has missing/renamed columns

---

## ❌ Current Error

```
pymysql.err.OperationalError: (1054, "Unknown column 'grpo_documents.qc_approver_id' in 'field list'")
```

**Root Cause**: Your MySQL database schema is outdated and doesn't match the current application models.

---

## 📋 Missing/Renamed Fields

### `grpo_documents` Table Issues:

| Old Column Name | New Column Name | Type | Status |
|----------------|-----------------|------|--------|
| `qc_user_id` | `qc_approver_id` | INT | ⚠️ RENAMED |
| (missing) | `warehouse_code` | VARCHAR(10) | ⚠️ MISSING |
| (missing) | `updated_at` | TIMESTAMP | ⚠️ MISSING |

### `grpo_items` Table Issues:

| Old Column Name | New Column Name | Type | Status |
|----------------|-----------------|------|--------|
| `grpo_document_id` | `grpo_id` | INT | ⚠️ RENAMED |
| (missing) | `line_total` | DECIMAL(15,2) | ⚠️ MISSING |
| (missing) | `base_entry` | INT | ⚠️ MISSING |
| (missing) | `base_line` | INT | ⚠️ MISSING |
| (missing) | `batch_required` | VARCHAR(1) | ⚠️ MISSING |
| (missing) | `serial_required` | VARCHAR(1) | ⚠️ MISSING |
| (missing) | `manage_method` | VARCHAR(1) | ⚠️ MISSING |
| (missing) | `updated_at` | TIMESTAMP | ⚠️ MISSING |
| `expiration_date` | `expiry_date` | DATE | ⚠️ RENAMED |
| `supplier_barcode` | `barcode` | VARCHAR(100) | ⚠️ RENAMED |
| `quantity` | `quantity` | DECIMAL(15,3) | ⚠️ PRECISION CHANGE |
| `received_quantity` | `received_quantity` | DECIMAL(15,3) | ⚠️ PRECISION CHANGE |

### Obsolete Columns (to be removed):
- ❌ `generated_barcode`
- ❌ `barcode_printed`
- ❌ `qc_notes` (moved to document level)
- ❌ `po_quantity` (replaced by `quantity`)
- ❌ `open_quantity` (replaced by `quantity`)

---

## 🔧 Solution: Choose ONE Method

### ✅ METHOD 1: Automated Python Script (RECOMMENDED)

**Best for**: Existing databases with data you want to keep

**Steps**:

1. **Edit database credentials** in `mysql_grpo_update_existing.py`:
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'user': 'root',        # ← Change this
       'password': 'your_password',  # ← Change this
       'database': 'wms_db',  # ← Change this if different
       'charset': 'utf8mb4'
   }
   ```

2. **Run the update script**:
   ```bash
   python mysql_grpo_update_existing.py
   ```

3. **Follow the prompts** - the script will:
   - Show what database it's connecting to
   - Ask for confirmation
   - Create automatic backup
   - Add/rename columns safely
   - Show detailed progress
   - Verify the final schema

**Advantages**:
- ✅ Automatically creates backups
- ✅ Safe - only adds missing columns
- ✅ Detailed progress reporting
- ✅ Keeps all your existing data
- ✅ Skips columns that already exist

---

### ✅ METHOD 2: Manual SQL Script

**Best for**: Manual database administrators

**Steps**:

1. **Backup your database first**:
   ```bash
   mysqldump -u root -p wms_db > wms_db_backup_$(date +%Y%m%d).sql
   ```

2. **Edit** `mysql_grpo_schema_update.sql` and uncomment the database name:
   ```sql
   USE wms_db;  -- Change 'wms_db' to your database name
   ```

3. **Run the SQL script**:
   ```bash
   mysql -u root -p wms_db < mysql_grpo_schema_update.sql
   ```

   **OR** run it interactively:
   ```bash
   mysql -u root -p wms_db
   source mysql_grpo_schema_update.sql;
   ```

**Note**: This script will show errors for columns that already exist - this is normal and safe to ignore.

---

### ✅ METHOD 3: Fresh Database Installation

**Best for**: Testing/development with no important data

**Steps**:

1. **Drop and recreate database**:
   ```bash
   mysql -u root -p
   ```
   ```sql
   DROP DATABASE wms_db;
   CREATE DATABASE wms_db;
   exit
   ```

2. **Run the fresh migration**:
   ```bash
   python mysql_consolidated_migration.py
   ```

**Warning**: ⚠️ This will DELETE ALL DATA in your database!

---

## 🔍 Verification Steps

After running any method, verify the schema:

```sql
-- Connect to MySQL
mysql -u root -p wms_db

-- Check grpo_documents structure
DESCRIBE grpo_documents;

-- Check grpo_items structure
DESCRIBE grpo_items;

-- Expected columns for grpo_documents:
-- id, po_number, supplier_code, supplier_name, warehouse_code,
-- user_id, qc_approver_id, qc_approved_at, qc_notes, status,
-- po_total, sap_document_number, notes, created_at, updated_at

-- Expected columns for grpo_items:
-- id, grpo_id, item_code, item_name, quantity, received_quantity,
-- unit_price, line_total, unit_of_measure, warehouse_code,
-- bin_location, batch_number, serial_number, expiry_date, barcode,
-- qc_status, po_line_number, base_entry, base_line, batch_required,
-- serial_required, manage_method, created_at, updated_at
```

---

## ✅ Testing Checklist

After updating your MySQL database:

- [ ] Start your Flask application
- [ ] Login to the system
- [ ] Navigate to GRPO module
- [ ] Create a new GRPO document
- [ ] Add items to the GRPO
- [ ] Save the GRPO
- [ ] Verify no errors in the console
- [ ] Check that data is saved correctly

---

## 🆘 Troubleshooting

### Issue: "Column already exists" errors
**Solution**: This is normal - the scripts are designed to be safe and skip existing columns.

### Issue: "Can't DROP - check that column/key exists"
**Solution**: This is normal - means the column doesn't exist yet, which is fine.

### Issue: Still getting "Unknown column" errors
**Solutions**:
1. Verify you're connected to the correct database
2. Check the DESCRIBE output matches expected schema
3. Restart your Flask application after database update
4. Clear any database connection pools

### Issue: Data loss after migration
**Solution**: Restore from backup:
```sql
-- For Python script backups:
DROP TABLE grpo_items;
CREATE TABLE grpo_items AS SELECT * FROM grpo_items_backup_YYYYMMDD_HHMMSS;

-- For manual SQL backups:
mysql -u root -p wms_db < wms_db_backup_YYYYMMDD.sql
```

---

## 📊 Complete Field Mapping Reference

### grpo_documents - Complete Schema

```sql
CREATE TABLE grpo_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    po_number VARCHAR(50) NOT NULL,
    supplier_code VARCHAR(20),
    supplier_name VARCHAR(100),
    warehouse_code VARCHAR(10),              -- ← NEW
    user_id INT NOT NULL,
    qc_approver_id INT,                      -- ← RENAMED from qc_user_id
    qc_approved_at TIMESTAMP NULL,
    qc_notes TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    po_total DECIMAL(15,2),
    sap_document_number VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- ← NEW
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (qc_approver_id) REFERENCES users(id),
    INDEX idx_po_number (po_number),
    INDEX idx_status (status),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

### grpo_items - Complete Schema

```sql
CREATE TABLE grpo_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grpo_id INT NOT NULL,                    -- ← RENAMED from grpo_document_id
    item_code VARCHAR(50) NOT NULL,
    item_name VARCHAR(200),
    quantity DECIMAL(15,3) NOT NULL,         -- ← PRECISION CHANGED
    received_quantity DECIMAL(15,3) DEFAULT 0,  -- ← PRECISION CHANGED
    unit_price DECIMAL(15,4),
    line_total DECIMAL(15,2),                -- ← NEW
    unit_of_measure VARCHAR(10),
    warehouse_code VARCHAR(10),
    bin_location VARCHAR(200),
    batch_number VARCHAR(50),
    serial_number VARCHAR(50),
    expiry_date DATE,                        -- ← RENAMED from expiration_date
    barcode VARCHAR(100),                    -- ← RENAMED from supplier_barcode
    qc_status VARCHAR(20) DEFAULT 'pending',
    po_line_number INT,
    base_entry INT,                          -- ← NEW (SAP PO DocEntry)
    base_line INT,                           -- ← NEW (SAP PO Line Number)
    batch_required VARCHAR(1) DEFAULT 'N',   -- ← NEW
    serial_required VARCHAR(1) DEFAULT 'N',  -- ← NEW
    manage_method VARCHAR(1) DEFAULT 'N',    -- ← NEW
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- ← NEW
    FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE,
    INDEX idx_grpo_id (grpo_id),
    INDEX idx_item_code (item_code),
    INDEX idx_qc_status (qc_status)
);
```

---

## 📚 Files Included

1. **`mysql_grpo_update_existing.py`** - Automated Python migration script (RECOMMENDED)
2. **`mysql_grpo_schema_update.sql`** - Manual SQL migration script
3. **`mysql_consolidated_migration.py`** - Fresh database installation script
4. **`MYSQL_GRPO_MISSING_FIELDS_FIX.md`** - This guide

---

## ⚠️ Important Notes

1. **Always backup before making changes** - This cannot be stressed enough!
2. **Run updates on a test database first** if possible
3. **The Python script is safer** than manual SQL for existing data
4. **Restart your Flask application** after database changes
5. **Verify the schema** after migration using DESCRIBE commands

---

## ✅ Success Criteria

Your migration is successful when:

1. ✅ No errors when starting Flask application
2. ✅ Can access GRPO module without errors
3. ✅ Can create new GRPO documents
4. ✅ Can add items to GRPO
5. ✅ DESCRIBE commands show all expected columns
6. ✅ No "Unknown column" errors in logs

---

**Last Updated**: October 22, 2025  
**Migration Scripts Version**: 2.0  
**Tested On**: MySQL 8.0, Python 3.11, Flask-SQLAlchemy 3.x
