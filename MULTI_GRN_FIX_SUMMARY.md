# Multi GRN Module - Purchase Order Display Fix

## Date: October 14, 2025

## Issue Identified
The Multi GRN Module was fetching open Purchase Orders from SAP but not displaying them in the UI.

## Root Cause
The SAP API filter was using `CardCode` instead of `CardName`:
- **Previous filter**: `CardCode eq '3D SPL'` (CardCode value)
- **Working filter**: `CardName eq '3D SEALS PRIVATE LIMITED'` (CardName value)

The system was correctly storing both CardCode and CardName in Step 1, but Step 2 was trying to fetch POs using CardCode when SAP required CardName for this query.

## Solution Implemented

### 1. Created New Service Method
- **File**: `modules/multi_grn_creation/services.py`
- **New Method**: `fetch_open_purchase_orders_by_name(card_name)`
- **Filter**: Uses `CardName eq '{card_name}'` instead of `CardCode`

### 2. Updated Routes
- **File**: `modules/multi_grn_creation/routes.py`
- **Step 2** (Line 101): Changed from `fetch_open_purchase_orders(batch.customer_code)` to `fetch_open_purchase_orders_by_name(batch.customer_name)`
- **Step 3** (Line 155): Changed from `fetch_open_purchase_orders(batch.customer_code)` to `fetch_open_purchase_orders_by_name(batch.customer_name)`

### 3. Maintained Backward Compatibility
- Kept the original `fetch_open_purchase_orders(card_code)` method for other modules that might use CardCode

## MySQL Migration Status
✅ The MySQL migration file `mysql_multi_grn_migration.py` is already up to date and includes all required tables:
- `multi_grn_batches` - Main batch records
- `multi_grn_po_links` - Links between batches and POs
- `multi_grn_line_selections` - Selected line items

## Testing
The fix has been deployed and the application is running successfully. The Multi GRN module should now:
1. Display open Purchase Orders when filtering by CardName
2. Show the PO list correctly in the UI
3. Allow users to select POs for batch GRN creation

## API Example
**Working SAP Query**:
```
https://192.168.1.4:50000/b1s/v1/PurchaseOrders?$filter=CardName eq '3D SEALS PRIVATE LIMITED' and DocumentStatus eq 'bost_Open'
```

This query now matches what the Multi GRN module uses internally.
