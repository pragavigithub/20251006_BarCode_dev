# ⚡ Quick Fix Guide - GRPO MySQL Missing Fields

## 🔴 Problem
```
ERROR: Unknown column 'grpo_documents.qc_approver_id' in 'field list'
```

## ✅ Solution (3 Simple Steps)

### Step 1: Edit Database Credentials

Open `mysql_grpo_update_existing.py` and update lines 19-24:

```python
DB_CONFIG = {
    'host': 'localhost',          # Your MySQL host
    'user': 'root',               # Your MySQL username
    'password': 'your_password',  # Your MySQL password
    'database': 'wms_db',         # Your database name
    'charset': 'utf8mb4'
}
```

### Step 2: Run the Update Script

```bash
python mysql_grpo_update_existing.py
```

When prompted, type `yes` to confirm.

### Step 3: Test Your Application

1. Restart your Flask application
2. Login to the WMS
3. Try creating a GRPO document
4. Should work without errors! ✅

---

## 📊 What This Fixes

### In `grpo_documents` table:
- ✅ Renames `qc_user_id` → `qc_approver_id`
- ✅ Adds `warehouse_code` column
- ✅ Adds `updated_at` column

### In `grpo_items` table:
- ✅ Renames `grpo_document_id` → `grpo_id`
- ✅ Adds 7 new fields: `line_total`, `base_entry`, `base_line`, `batch_required`, `serial_required`, `manage_method`, `updated_at`
- ✅ Renames `expiration_date` → `expiry_date`
- ✅ Renames `supplier_barcode` → `barcode`
- ✅ Updates quantity precision
- ✅ Removes obsolete columns

---

## 🆘 Need Help?

Read the complete guide: **`MYSQL_GRPO_MISSING_FIELDS_FIX.md`**

---

## ✅ Verification

After running the script, check:

```sql
mysql -u root -p
USE wms_db;
DESCRIBE grpo_documents;
DESCRIBE grpo_items;
```

You should see all the new columns listed above.

---

**Estimated Time**: 2-5 minutes  
**Backup**: Automatically created by the script  
**Risk Level**: Low (script is safe and reversible)
