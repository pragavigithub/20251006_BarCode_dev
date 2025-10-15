# Database Migration Log

## Purpose
This file tracks all database schema changes chronologically. Each migration represents a specific change to the database structure.

## Current Database Version
- **PostgreSQL (Primary)**: Latest schema from models
- **MySQL (Secondary)**: Tracked via migrations below

---

## Migration History

### 2025-10-13 - Initial Schema
- **File**: `mysql/schema/initial_schema.sql`
- **Description**: Initial database schema for Warehouse Management System
- **Tables Created**: 
  - Core: users, branches, user_sessions, password_reset_tokens
  - GRPO: grpo_documents, grpo_items
  - Inventory: inventory_transfers, inventory_transfer_items
  - Multi GRN: multi_grn_batches, multi_grn_po_links, multi_grn_line_selections
  - Pick List: pick_lists, pick_list_items, pick_list_lines, pick_list_bin_allocations
  - Serial: serial_number_transfers, serial_number_transfer_items, serial_number_transfer_serials
  - Serial Item: serial_item_transfers, serial_item_transfer_items
  - Supporting: bin_locations, bin_items, bin_scanning_logs, barcode_labels, qr_code_labels, document_number_series, inventory_counts, inventory_count_items, sales_orders, sales_order_lines
- **Status**: ✅ Documented
- **Applied By**: System
- **Notes**: 
  - Baseline schema from SQLAlchemy models
  - **Fixes Applied**: 
    - Added missing `created_by` column to `password_reset_tokens` table (INT, nullable, foreign key to users.id)
    - Corrected `password_reset_tokens.token` column from VARCHAR(255) to VARCHAR(256) to match SQLAlchemy model
  - Schema validated and ready for MySQL deployment

---

## Future Migrations
Add new migrations below in reverse chronological order (newest first).

### 2025-10-15 - GRPO Item Validation Fields (Batch/Serial Requirements)
- **File**: `mysql_grpo_item_validation_migration.py`
- **Description**: Added ItemCode validation fields to GRPO items for batch and serial number management
- **Tables Affected**: grpo_items
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - Added `batch_required` VARCHAR(1) DEFAULT 'N' to `grpo_items` - Indicates if batch number is required (Y/N)
  - Added `serial_required` VARCHAR(1) DEFAULT 'N' to `grpo_items` - Indicates if serial number is required (Y/N)
  - Added `manage_method` VARCHAR(1) DEFAULT 'N' to `grpo_items` - Item management method (A=Average, R=FIFO/Release, N=None)
- **API Integration**:
  - Added SAP API method `validate_item_code()` in `sap_integration.py` to call SQLQuery 'ItemCode_Batch_Serial_Val'
  - Added validation endpoint `/grpo/validate-item/<item_code>` in GRPO routes
  - Frontend dynamically enables/disables batch and serial number fields based on SAP validation
- **Notes**: 
  - Validation is performed via SAP B1 SQL Query: `SQLQueries('ItemCode_Batch_Serial_Val')/List`
  - Fields are dynamically enabled/disabled in the GRPO detail modal based on item properties
  - Supports FIFO/Release method (R) for quantity-based management

---

### 2025-10-14 - MultiGRN Serial/Batch Number Support and Barcode Generation
- **File**: `mysql/changes/2025-10-14_multi_grn_enhancements.sql`
- **Description**: Added serial/batch number support and barcode generation to MultiGRN module
- **Tables Affected**: multi_grn_batches, multi_grn_line_selections
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - Added `batch_number` VARCHAR(50) UNIQUE column to `multi_grn_batches` for better tracking
  - Added `serial_numbers` TEXT column to `multi_grn_line_selections` to store serial number data (JSON format)
  - Added `batch_numbers` TEXT column to `multi_grn_line_selections` to store batch number data (JSON format)
  - Added `barcode_generated` BOOLEAN column to `multi_grn_line_selections` to track barcode generation status
  - Created index on `multi_grn_batches.batch_number` for faster lookups
  - Created index on `multi_grn_line_selections.barcode_generated` for filtering
- **Notes**: 
  - Serial and batch numbers are stored as JSON text for flexibility with SAP B1 API format
  - Batch numbers are auto-generated with format: MGRN-YYYYMMDDHHmmss
  - Barcode generation API endpoint added at `/multi-grn/api/generate-barcode`

---

### Template for New Migration Entry
```markdown
### YYYY-MM-DD HH:MM - Migration Title
- **File**: `mysql/changes/YYYY-MM-DD_HH-MM_description.sql`
- **Description**: Brief description of changes
- **Tables Affected**: table1, table2
- **Status**: ✅ Applied / ⏳ Pending / ❌ Failed / 🔄 Rolled Back
- **Applied By**: Developer Name
- **Notes**: Any important notes or dependencies
```

---

## Migration Guidelines

### When to Create a Migration
1. Adding/removing tables
2. Adding/removing columns
3. Changing column types or constraints
4. Adding/removing indexes
5. Modifying foreign key relationships
6. Data transformations

### Migration Checklist
- [ ] Create migration file with proper naming
- [ ] Include UP and DOWN SQL
- [ ] Add entry to this log
- [ ] Test on development database
- [ ] Document any manual steps required
- [ ] Update schema documentation if needed

### Rollback Procedure
If a migration needs to be rolled back:
1. Run the DOWN SQL (from comments in migration file)
2. Update status in this log to 🔄 Rolled Back
3. Document reason for rollback
4. Create new migration if changes are still needed

---

## Notes
- This system tracks MySQL migrations for secondary database support
- Primary PostgreSQL database uses SQLAlchemy ORM migrations
- Always keep this log updated when making schema changes
- Each migration should be atomic and reversible