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