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

### 2025-10-26 - Direct Inventory Transfer Module
- **File**: `mysql/changes/2025-10-26_direct_inventory_transfer_module.sql`
- **Description**: Added complete Direct Inventory Transfer module for barcode-driven warehouse transfers
- **Tables Created**: 
  - `direct_inventory_transfers` - Transfer document headers
  - `direct_inventory_transfer_items` - Transfer line items with batch/serial support
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - **direct_inventory_transfers Table**:
    - `id` INT PRIMARY KEY AUTO_INCREMENT
    - `transfer_number` VARCHAR(50) UNIQUE - Document number
    - `sap_document_number` VARCHAR(50) - SAP B1 document reference
    - `status` VARCHAR(20) - draft, submitted, qc_approved, posted, rejected
    - `user_id` INT - Creator user reference (FK to users)
    - `qc_approver_id` INT - QC approver reference (FK to users)
    - `qc_approved_at` DATETIME - QC approval timestamp
    - `qc_notes` TEXT - QC approval/rejection notes
    - `from_warehouse` VARCHAR(50) - Source warehouse code
    - `to_warehouse` VARCHAR(50) - Destination warehouse code
    - `from_bin` VARCHAR(50) - Source bin location
    - `to_bin` VARCHAR(50) - Destination bin location
    - `notes` TEXT - Transfer notes
    - `created_at` DATETIME - Creation timestamp
    - `updated_at` DATETIME - Last update timestamp
  - **direct_inventory_transfer_items Table**:
    - `id` INT PRIMARY KEY AUTO_INCREMENT
    - `direct_inventory_transfer_id` INT - Parent transfer reference (FK, CASCADE DELETE)
    - `item_code` VARCHAR(50) - SAP item code
    - `item_description` VARCHAR(200) - Item description
    - `barcode` VARCHAR(100) - Scanned barcode value
    - `item_type` VARCHAR(20) - serial, batch, or none
    - `quantity` DECIMAL(15,2) - Transfer quantity
    - `unit_of_measure` VARCHAR(10) - UOM (default 'EA')
    - `from_warehouse_code` VARCHAR(50) - Source warehouse
    - `to_warehouse_code` VARCHAR(50) - Destination warehouse
    - `from_bin_code` VARCHAR(50) - Source bin
    - `to_bin_code` VARCHAR(50) - Destination bin
    - `batch_number` VARCHAR(100) - Batch number for batch-managed items
    - `serial_numbers` TEXT - JSON array of serial numbers for serial-managed items
    - `qc_status` VARCHAR(20) - pending, approved, rejected
    - `validation_status` VARCHAR(20) - pending, validated, failed
    - `validation_error` TEXT - Validation error messages
    - `created_at` DATETIME - Creation timestamp
    - `updated_at` DATETIME - Last update timestamp
  - **Document Number Series**:
    - Added 'DIRECT_INVENTORY_TRANSFER' series with prefix 'DIT'
- **Application Enhancements**:
  - Added custom Jinja2 filter `from_json` for parsing JSON serial numbers in templates
  - Integrated SAP B1 validation for item codes and warehouse/bin locations
  - Automatic detection of serial/batch managed items via SAP API
  - QC approval workflow before posting to SAP B1
  - Dynamic form fields based on item management type
- **Routes Added**: 
  - `/direct-inventory-transfer/` - Index page with pagination
  - `/direct-inventory-transfer/create` - Create new transfer
  - `/direct-inventory-transfer/<id>` - Transfer detail view
  - `/direct-inventory-transfer/<id>/add_item` - Add item via barcode
  - `/direct-inventory-transfer/<id>/submit` - Submit for QC approval
  - `/direct-inventory-transfer/<id>/approve` - QC approve and post to SAP
  - `/direct-inventory-transfer/<id>/reject` - QC reject transfer
  - `/direct-inventory-transfer/api/validate-item` - Validate item code from SAP
  - `/direct-inventory-transfer/api/get-warehouses` - Fetch warehouse list
  - `/direct-inventory-transfer/api/get-bins` - Fetch bin locations
- **Notes**: 
  - Fully integrated with SAP B1 Service Layer API
  - Supports serial and batch number tracking
  - QC approval workflow ensures data quality
  - Barcode-driven scanning for warehouse efficiency
  - Custom filter required to parse JSON serial numbers in templates

### 2025-10-15 - SAP B1 JSON Consolidation Fixes
- **File**: `sap_integration.py` (create_purchase_delivery_note method)
- **Description**: Fixed critical bugs in SAP B1 Purchase Delivery Note JSON generation
- **Status**: ✅ Completed
- **Changes**:
  - **SerialNumbers Array**:
    - Fixed `BaseLineNumber` to use PO BaseLine (`po_line_num`) instead of document line counter
    - Fixed `Quantity` to always be 1.0 for each serial entry (SAP requirement)
    - Fixed line-level `Quantity` to sum all serial quantities correctly
    - Fixed date format to YYYY-MM-DD (removed ISO timestamp format)
    - Added proper ManufactureDate and Notes fields
  - **BatchNumbers Array**:
    - Fixed `BaseLineNumber` to use PO BaseLine (`po_line_num`) instead of document line counter
    - Fixed line-level `Quantity` to sum all batch quantities correctly
    - Ensured proper quantity calculation from batch records
- **SAP B1 Integration**:
  - JSON now matches exact SAP B1 Service Layer API format
  - Properly consolidates serial/batch data for posting
  - Eliminates "Quantity: 0.0" errors
  - Fixes BaseLineNumber reference issues
- **Impact**: Critical fix for GRPO posting to SAP B1
- **Notes**: 
  - Validated against user-provided SAP B1 JSON examples
  - Architect-reviewed and approved
  - Ready for production testing

### 2025-10-15 - GRPO Serial and Batch Number Tables
- **File**: `mysql_grpo_serial_batch_migration.py`
- **Description**: Added dedicated tables for serial and batch number management with barcode support
- **Tables Created**: 
  - `grpo_serial_numbers` - Individual serial number tracking
  - `grpo_batch_numbers` - Batch number tracking with quantities
- **Status**: ⏳ Pending
- **Changes**:
  - **grpo_serial_numbers**:
    - `id` INT AUTO_INCREMENT PRIMARY KEY
    - `grpo_item_id` INT NOT NULL (FK to grpo_items)
    - `manufacturer_serial_number` VARCHAR(100) - Manufacturer's serial number
    - `internal_serial_number` VARCHAR(100) UNIQUE NOT NULL - Internal tracking serial (must be unique)
    - `expiry_date` DATE - Expiration date
    - `manufacture_date` DATE - Manufacturing date
    - `notes` TEXT - Additional notes
    - `barcode` VARCHAR(200) - Base64 encoded barcode image
    - `quantity` DECIMAL(15,3) DEFAULT 1.0 - Quantity (typically 1 for serial items)
    - `base_line_number` INT DEFAULT 0 - SAP base line reference
    - `created_at` DATETIME
  - **grpo_batch_numbers**:
    - `id` INT AUTO_INCREMENT PRIMARY KEY
    - `grpo_item_id` INT NOT NULL (FK to grpo_items)
    - `batch_number` VARCHAR(100) NOT NULL - Batch identifier
    - `quantity` DECIMAL(15,3) NOT NULL - Batch quantity
    - `base_line_number` INT DEFAULT 0 - SAP base line reference
    - `manufacturer_serial_number` VARCHAR(100) - Optional manufacturer serial
    - `internal_serial_number` VARCHAR(100) - Optional internal serial
    - `expiry_date` DATE - Batch expiration date
    - `barcode` VARCHAR(200) - Base64 encoded barcode image
    - `created_at` DATETIME
- **SAP B1 Integration**:
  - Supports SAP DocumentLines SerialNumbers array format
  - Supports SAP DocumentLines BatchNumbers array format
  - Each serial entry generates unique barcode for tracking
- **Notes**: 
  - Internal serial numbers must be unique across the system
  - Supports quantity-based entry for serial items
  - Barcode generation using QRCode library

---

### 2025-10-17 - GRPO Dynamic Batch/Serial Field UI Enhancement
- **File**: `modules/grpo/templates/grpo_detail.html`
- **Description**: Enhanced GRPO module with dynamic batch/serial number field management based on SAP item validation
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - **Dynamic Field Control**:
    - Added JavaScript function `validateItemCodeFromSAP()` to fetch item validation from SAP B1
    - Implemented automatic show/hide logic for Batch Number vs Serial Number fields
    - Fields now dynamically enable based on SAP ItemCode validation response (BatchNum='Y' or SerialNum='Y')
  - **Serial Number Management**:
    - Added `serial_section` container with dynamic serial number input generation
    - Serial inputs automatically generated based on received quantity (up to 100 items)
    - Each serial number input includes barcode generation capability
    - Added `prepareSerialDataForSubmit()` function to collect serial data as JSON before form submission
  - **Batch Number Management**:
    - Batch fields shown only when item is batch-managed (BatchNum='Y')
    - Expiration date field linked to batch selection
  - **Barcode Generation**:
    - Automatic barcode generation for each serial number with format `SN:{ItemCode}-{SerialNumber}`
    - Visual barcode preview for individual serial entries
  - **Validation**:
    - Client-side validation ensures all serial numbers are entered before submission
    - Serial data stored in hidden field `serial_numbers_json` as JSON array
    - Backend validates serial count matches received quantity
- **API Integration**:
  - Uses existing `/grpo/validate-item/<item_code>` endpoint to fetch item management type
  - Response fields: `batch_required`, `serial_required`, `manage_method`
  - Integrates with SAP B1 SQL Query 'ItemCode_Batch_Serial_Val'
- **User Experience**:
  - Clean, intuitive interface showing only relevant fields
  - No manual dropdown switching - fields appear automatically
  - Quantity change triggers serial input regeneration
  - Supports up to 100 serial numbers via UI (with bulk upload fallback for larger quantities)
- **Database Impact**: No schema changes - uses existing `grpo_serial_numbers` and `grpo_batch_numbers` tables
- **Notes**: 
  - Frontend-only enhancement, no backend route changes required
  - Compatible with existing GRPO workflow and SAP B1 posting logic
  - Improves data entry efficiency for warehouse operators

---

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

### 2025-10-15 - GRPO Automatic Barcode Generation Enhancement
- **File**: `mysql/changes/2025-10-15_grpo_barcode_enhancements.sql`
- **Description**: Enhanced GRPO module with automatic barcode generation for serial and batch managed items
- **Tables Affected**: grpo_serial_numbers, grpo_batch_numbers (existing tables)
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - **Application Logic Enhancements**:
    - Auto-detect item type (Serial/Batch/Non-Batch) via SAP B1 API endpoint `SQLQueries('ItemCode_Batch_Serial_Val')/List`
    - Automatically generate QR code barcodes when serial/batch items are added to GRPO
    - Store barcodes as base64 encoded PNG images in database
    - Display barcodes in GRPO detail view for scanning/printing
  - **Barcode Formats**:
    - Serial Items: `SN:{internal_serial_number}`
    - Batch Items: `BATCH:{batch_number}`
  - **JavaScript Enhancements**:
    - Real-time item type validation on item code entry
    - Dynamic show/hide of serial/batch input fields
    - Automatic serial number input generation based on quantity
  - **SAP B1 Integration**:
    - JSON consolidation for Purchase Delivery Note creation
    - Proper SerialNumbers and BatchNumbers array formatting
    - Support for ManufacturerSerialNumber, InternalSerialNumber, ExpiryDate, ManufactureDate
- **Routes Updated**: 
  - `/grpo/<grpo_id>/add_item` - Enhanced with barcode generation
  - `/grpo/validate-item/<item_code>` - Item type validation via SAP
- **Notes**: 
  - No schema changes required - barcode fields already existed
  - Enhancement focuses on automatic generation and proper SAP integration
  - Barcodes generated using QRCode library with error correction level L

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