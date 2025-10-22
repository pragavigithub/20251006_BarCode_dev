# MySQL GRPO Module Migration Guide

**Last Updated**: October 22, 2025  
**Purpose**: Document database schema for GRPO (Goods Receipt PO) Module with Batch/Serial Number Management

## Overview

This guide documents the MySQL database schema for the GRPO module that handles goods receipts against purchase orders with support for:
- Serial number managed items
- Batch managed items  
- Standard (non-managed) items
- SAP B1 integration for validation and posting

## SAP Integration

### Item Validation Endpoint

**URL**: `https://{SAP_SERVER}:50000/b1s/v1/SQLQueries('ItemCode_Batch_Serial_Val')/List`  
**Method**: POST  
**Purpose**: Determine if an item is batch-managed, serial-managed, or standard

**Request Body**:
```json
{
    "ParamList": "itemCode='<ITEM_CODE>'"
}
```

**Response**:
```json
{
    "odata.metadata": "https://{SAP_SERVER}:50000/b1s/v1/$metadata#SAPB1.SQLQueryResult",
    "SqlText": "Select T0.[ItemCode], IsNULL(T0.[ManBtchNum],'N') as [BatchNum] ,IsNULL(T0.[ManSerNum],'N') as [SerialNum],IsNULL(T0.[MngMethod],'N')  as [NonBatch_NonSerialMethod] FROM [OITM] T0 WHERE T0.[ItemCode]=:itemCode",
    "value": [
        {
            "BatchNum": "N",
            "ItemCode": "S1",
            "NonBatch_NonSerialMethod": "A",
            "SerialNum": "Y"
        }
    ]
}
```

**Field Descriptions**:
- `BatchNum`: 'Y' if batch managed, 'N' otherwise
- `SerialNum`: 'Y' if serial number managed, 'N' otherwise
- `NonBatch_NonSerialMethod`: 'A' (Average), 'R' (FIFO/Release), 'N' (None)

### GRPO Posting Endpoint

**URL**: `https://{SAP_SERVER}:50000/b1s/v1/PurchaseDeliveryNotes`  
**Method**: POST  
**Purpose**: Post GRPO to SAP B1 after QC approval

**Request Body Example** (with Serial and Batch items):
```json
{
   "CardCode":"3D SPL",
   "DocDate":"2025-10-13",
   "DocDueDate":"2025-10-13",
   "Comments":"Auto-created from PO after QC",
   "NumAtCard":"EXT-REF-20251015-002",
   "BPL_IDAssignedToInvoice":5,
   "DocumentLines":[
      {
         "BaseType":22,
         "BaseEntry":3641,
         "BaseLine":0,
         "ItemCode":"S1",
         "Quantity":2.0,
         "WarehouseCode":"7000-FG",
         "SerialNumbers":[
            {
               "Quantity":1.0,
               "BaseLineNumber":0,
               "ManufacturerSerialNumber": "MFG-SN-009",
               "InternalSerialNumber": "INT-SN-009",
               "ExpiryDate": "2025-10-18",
               "ManufactureDate": "2025-10-13",
               "Notes": "Auto-created from PO"
            },
            {
               "Quantity":1.0,
               "BaseLineNumber":0,
               "ManufacturerSerialNumber": "MFG-SN-010",
               "InternalSerialNumber": "INT-SN-010",
               "ExpiryDate": "2025-10-18",
               "ManufactureDate": "2025-10-13",
               "Notes": "Auto-created from PO"
            }
         ]
      },
      {
         "BaseType":22,
         "BaseEntry":3641,
         "BaseLine":2,
         "ItemCode":"1248-114497",
         "Quantity":10.0,
         "WarehouseCode":"7000-FG",
         "BatchNumbers":[
            {
               "BatchNumber":"4834800422",
               "Quantity":10.0,
               "BaseLineNumber":1,
               "ManufacturerSerialNumber":"MFG-SN-001",
               "InternalSerialNumber":"INT-SN-001",
               "ExpiryDate":"2025-10-17T00:00:00Z"
            }
         ]
      }
   ]
}
```

## Database Schema

### Table: grpo_documents

Main GRPO document header table.

```sql
CREATE TABLE grpo_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    po_number VARCHAR(50) NOT NULL,
    supplier_code VARCHAR(20),
    supplier_name VARCHAR(100),
    warehouse_code VARCHAR(10),
    user_id INT NOT NULL,
    qc_approver_id INT,
    qc_approved_at DATETIME,
    qc_notes TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    po_total DECIMAL(15, 2),
    sap_document_number VARCHAR(50),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (qc_approver_id) REFERENCES user(id),
    
    INDEX idx_po_number (po_number),
    INDEX idx_status (status),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Status Values**:
- `draft`: Initial state, being edited
- `submitted`: Submitted for QC approval
- `qc_approved`: Approved by QC but not yet posted to SAP
- `posted`: Successfully posted to SAP B1
- `rejected`: Rejected by QC

### Table: grpo_items

GRPO line items with batch/serial management support.

```sql
CREATE TABLE grpo_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grpo_id INT NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    item_name VARCHAR(200),
    quantity DECIMAL(15, 3) NOT NULL,
    received_quantity DECIMAL(15, 3) DEFAULT 0,
    unit_price DECIMAL(15, 4),
    line_total DECIMAL(15, 2),
    unit_of_measure VARCHAR(10),
    warehouse_code VARCHAR(10),
    bin_location VARCHAR(200),
    batch_number VARCHAR(50),
    serial_number VARCHAR(50),
    expiry_date DATE,
    barcode VARCHAR(100),
    qc_status VARCHAR(20) DEFAULT 'pending',
    po_line_number INT,
    base_entry INT COMMENT 'SAP PO DocEntry',
    base_line INT COMMENT 'SAP PO Line Number',
    
    -- Item validation metadata from SAP
    batch_required VARCHAR(1) DEFAULT 'N' COMMENT 'Y or N',
    serial_required VARCHAR(1) DEFAULT 'N' COMMENT 'Y or N',
    manage_method VARCHAR(1) DEFAULT 'N' COMMENT 'A (Average), R (FIFO/Release), N (None)',
    
    FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE,
    
    INDEX idx_grpo_id (grpo_id),
    INDEX idx_item_code (item_code),
    INDEX idx_qc_status (qc_status),
    INDEX idx_batch_number (batch_number),
    INDEX idx_serial_number (serial_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**QC Status Values**:
- `pending`: Awaiting QC approval
- `approved`: Approved by QC
- `rejected`: Rejected by QC

### Table: grpo_serial_numbers

Serial numbers for serial-managed items (supports multiple serials per item).

```sql
CREATE TABLE grpo_serial_numbers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grpo_item_id INT NOT NULL,
    manufacturer_serial_number VARCHAR(100),
    internal_serial_number VARCHAR(100) NOT NULL,
    expiry_date DATE,
    manufacture_date DATE,
    notes TEXT,
    barcode VARCHAR(200) COMMENT 'Base64 encoded barcode image',
    quantity DECIMAL(15, 3) DEFAULT 1.0,
    base_line_number INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (grpo_item_id) REFERENCES grpo_items(id) ON DELETE CASCADE,
    
    INDEX idx_grpo_item_id (grpo_item_id),
    INDEX idx_internal_serial (internal_serial_number),
    INDEX idx_manufacturer_serial (manufacturer_serial_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Table: grpo_batch_numbers

Batch numbers for batch-managed items (supports multiple batches per item).

```sql
CREATE TABLE grpo_batch_numbers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grpo_item_id INT NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    quantity DECIMAL(15, 3) NOT NULL,
    manufacturer_serial_number VARCHAR(100),
    internal_serial_number VARCHAR(100),
    expiry_date DATE,
    manufacture_date DATE,
    admission_date DATE,
    location VARCHAR(100),
    notes TEXT,
    base_line_number INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (grpo_item_id) REFERENCES grpo_items(id) ON DELETE CASCADE,
    
    INDEX idx_grpo_item_id (grpo_item_id),
    INDEX idx_batch_number (batch_number),
    INDEX idx_expiry_date (expiry_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Table: purchase_delivery_notes

Purchase Delivery Note records for SAP B1 posting.

```sql
CREATE TABLE purchase_delivery_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grpo_id INT NOT NULL,
    external_reference VARCHAR(50) UNIQUE,
    sap_document_number VARCHAR(50),
    supplier_code VARCHAR(20),
    warehouse_code VARCHAR(10),
    document_date DATE,
    due_date DATE,
    total_amount DECIMAL(15, 2),
    status VARCHAR(20) DEFAULT 'draft',
    json_payload TEXT COMMENT 'JSON sent to SAP',
    sap_response TEXT COMMENT 'SAP response',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    posted_at DATETIME,
    
    FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE,
    
    INDEX idx_grpo_id (grpo_id),
    INDEX idx_status (status),
    INDEX idx_sap_document_number (sap_document_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Status Values**:
- `draft`: Created but not posted
- `posted`: Successfully posted to SAP
- `cancelled`: Cancelled

## Migration from PostgreSQL to MySQL

### Key Differences

1. **Auto Increment**:
   - PostgreSQL: Uses `SERIAL` or `BIGSERIAL`
   - MySQL: Uses `AUTO_INCREMENT`

2. **Timestamps**:
   - PostgreSQL: Uses `TIMESTAMP WITH TIME ZONE`
   - MySQL: Uses `DATETIME` with `DEFAULT CURRENT_TIMESTAMP`

3. **Boolean Values**:
   - PostgreSQL: Native `BOOLEAN` type
   - MySQL: Uses `VARCHAR(1)` with 'Y'/'N' values

4. **Text Fields**:
   - PostgreSQL: Uses `TEXT`
   - MySQL: Uses `TEXT` (same)

5. **JSON Fields**:
   - PostgreSQL: Uses `JSONB`
   - MySQL: Uses `JSON` or `TEXT`

### Migration Script

```sql
-- Drop existing tables if migrating from PostgreSQL
DROP TABLE IF EXISTS grpo_batch_numbers;
DROP TABLE IF EXISTS grpo_serial_numbers;
DROP TABLE IF EXISTS purchase_delivery_notes;
DROP TABLE IF EXISTS grpo_items;
DROP TABLE IF EXISTS grpo_documents;

-- Create tables in MySQL
-- (Use CREATE TABLE statements from schema section above)
```

## Application Features

### 1. Item Type Detection

When adding an item to a GRPO:
1. User enters Item Code
2. System calls SAP validation endpoint
3. System determines item type based on response:
   - **Serial Managed**: `SerialNum = 'Y'`
   - **Batch Managed**: `BatchNum = 'Y'`
   - **Standard**: Both = 'N'

### 2. Dynamic Form Fields

Based on item type, the system shows:

**Serial Managed Items**:
- Serial number inputs (one per quantity unit)
- Each serial has:
  - Internal serial number
  - Manufacturer serial number
  - Expiry date
  - Manufacture date
  - Notes

**Batch Managed Items**:
- Batch number field
- Expiry date field
- Quantity field

**Standard Items**:
- No additional fields required

### 3. GRPO Workflow

```
1. Draft → User creates GRPO and adds items
2. Submitted → User submits for QC approval
3. QC Approved → QC reviewer approves
4. Posted → System posts to SAP B1 automatically
```

OR

```
1. Draft → User creates GRPO
2. Rejected → QC reviewer rejects with notes
3. Draft → User edits and resubmits
```

## Environment Variables Required

```bash
# SAP B1 Configuration
SAP_B1_SERVER=https://192.168.0.131:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=1422
SAP_B1_COMPANY_DB=SBODemoUS

# Database Configuration
DATABASE_URL=mysql://user:password@localhost:3306/wms_db
```

## API Endpoints

### Backend Routes (Python/Flask)

```python
# GRPO Management
GET    /grpo                          # List all GRPOs
GET    /grpo/create                   # Create new GRPO form
POST   /grpo/create                   # Create new GRPO
GET    /grpo/<id>                     # View GRPO details
POST   /grpo/<id>/add_item            # Add item to GRPO
POST   /grpo/<id>/submit              # Submit for QC
POST   /grpo/<id>/approve             # QC approve and post to SAP
POST   /grpo/<id>/reject              # QC reject

# Item Validation
GET    /grpo/validate-item/<item_code>  # Validate item from SAP

# Field Updates
POST   /grpo/item/<id>/update_field   # Update individual field
```

## Testing Checklist

- [ ] Create GRPO with serial-managed item
- [ ] Verify serial number inputs appear based on quantity
- [ ] Create GRPO with batch-managed item
- [ ] Verify batch fields appear
- [ ] Create GRPO with standard item
- [ ] Verify no batch/serial fields appear
- [ ] Submit GRPO for QC approval
- [ ] QC approve and verify SAP posting
- [ ] Verify serial numbers posted correctly to SAP
- [ ] Verify batch numbers posted correctly to SAP
- [ ] Test QC rejection workflow
- [ ] Verify re-submission after rejection

## Common Issues and Solutions

### Issue: Serial/Batch fields not appearing

**Solution**: 
1. Check SAP connection is active
2. Verify SQL Query 'ItemCode_Batch_Serial_Val' exists in SAP
3. Check browser console for validation errors
4. Verify item code exists in SAP

### Issue: Posting to SAP fails

**Solution**:
1. Check SAP session is active
2. Verify PO exists and is open in SAP
3. Check serial/batch quantities match
4. Review SAP response in database

### Issue: Duplicate item error

**Solution**:
Each item can only be received once per GRPO. If you need to receive more quantity, update the existing item or create a new GRPO.

## Future Enhancements

1. **Bulk Serial Upload**: Support CSV upload for large quantities
2. **Barcode Scanning**: Scan serial/batch numbers directly
3. **Auto-generation**: Auto-generate batch numbers if not provided
4. **SAP Bin Allocation**: Support bin-level allocation in SAP
5. **Multi-warehouse**: Support receiving to multiple warehouses in one GRPO

## References

- SAP Business One Service Layer API Documentation
- Flask-SQLAlchemy Documentation
- Bootstrap 5 Modal Components
- QRCode.js Library

---

**Document Version**: 1.0  
**Last Modified**: October 22, 2025  
**Author**: WMS Development Team
