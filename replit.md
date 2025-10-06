# Warehouse Management System (WMS)

## Overview
A Flask-based warehouse management system with SAP integration for barcode scanning, inventory management, goods receipt, pick lists, and inventory transfers.

## Project Architecture
- **Backend**: Flask web application
- **Database**: SQLite (configured as fallback with automatic initialization)
- **Frontend**: Server-side rendering with Jinja2 templates
- **Integration**: SAP B1 Service Layer API integration for warehouse operations
- **Authentication**: Flask-Login with role-based access control
- **Deployment**: Gunicorn with autoscale deployment configuration

## Key Features
- User authentication and role-based access control
- Goods Receipt Purchase Order (GRPO) management
- Inventory transfer requests
- Pick list management
- Barcode scanning integration
- Branch management
- Quality control dashboard

## Replit Environment Setup
- **Workflow**: Flask application runs via `uv run python main.py` on port 5000
- **Dependencies**: Managed via `pyproject.toml` and synchronized with `uv sync`
- **Database**: SQLite with automatic table creation and default admin user initialization
- **Default Login**: Username: `admin`, Password: `admin123`
- **Development Server**: Runs on 0.0.0.0:5000 with Flask debug mode enabled
- **Production Deployment**: Configured with Gunicorn autoscale deployment (4 workers)

## Recent Changes
- **2025-10-06**: Successfully migrated GitHub import to Replit environment
  - Configured SQLite database with automatic initialization
  - Set up development workflow with uv package manager
  - Added deployment configuration using Gunicorn
  - Fixed login form autocomplete attributes for better browser compatibility
  - **Changed credentials loading**: Now reads from JSON file (C:\tmp\sap_login\credential.json) instead of .env files
  - Created credentials_loader.py module for flexible credential management with environment variable fallback
  - **Enhanced GRPO Module with SAP Series Integration**:
    - Added PO Series dropdown selection in GRPO creation modal
    - Implemented SAP B1 SQLQueries API integration for fetching PO series (Get_PO_Series)
    - Added DocEntry retrieval based on series and document number (Get_PO_DocEntry)
    - Created three new API endpoints: /api/get-po-series, /api/get-doc-entry, /api/get-po-by-doc-entry
    - Updated GRPODocument model with po_series and po_doc_entry fields
    - Enhanced GRPO creation workflow to use DocEntry for more reliable PO retrieval
    - Created MySQL migration script (mysql_grpo_series_migration.py) for database schema updates
    - Improved frontend validation with real-time PO verification
- **2025-08-12**: Successfully migrated from Replit Agent to Replit environment
- Database connection configured to fallback to SQLite when MySQL unavailable
- Security configurations updated for production readiness
- MySQL migration file completely updated to align with current models
- All schema mismatches between models and MySQL migration file resolved
- Added missing tables: inventory_counts, inventory_count_items, barcode_labels, bin_locations
- Fixed GRPO and inventory transfer table schemas to match current implementation
- **2025-08-13**: Fixed QR code generation issue by adding missing column detection
- Added comprehensive column migration for `qr_code_labels` table including `item_name`, `po_number`, `bin_code`
- Migration file now handles existing databases with missing columns automatically
- Fixed legacy MySQL fields `label_number` and `qr_code_data` that were causing NOT NULL constraint errors
- Updated migration to handle all legacy QR code table schemas from previous implementations
- Enhanced GRPO module: "+Add Item" buttons are now disabled for closed PO lines and enabled for open lines
- Added status-based button management for better user experience and data integrity
- **2025-08-14**: Enhanced Picklist module with Sales Order integration
- Added SalesOrder and SalesOrderLine models to enable enhanced picklist functionality
- Implemented SAP B1 Sales Order API integration functions for fetching and syncing sales orders
- Updated picklist routes to enhance lines with Sales Order data including ItemCode, Customer details, and quantities
- Added Sales Order tables to MySQL migration file with proper indexing and foreign keys
- Enhanced picklist lines now display item details from matching Sales Orders based on OrderEntry and LineNum
- **2025-08-14**: Successfully migrated from Replit Agent to Replit environment
- Configured PostgreSQL database for Replit cloud environment
- **Fixed User Management System**: Updated user model from `user_is_active` to `is_active` for consistency
- **Enhanced User Management Routes**: Added missing routes for delete, activate, deactivate user functionality
- **Created edit_user.html template**: Complete user editing interface with permissions management
- **Fixed User Management Actions**: All action buttons (Edit, Delete, Reset Password, Activate/Deactivate) now fully functional
- **Added change_password.html template**: Password change functionality with validation
- **Updated MySQL Migration**: Synchronized database schema with model changes throughout all migration files
- **Fixed Branch Management**: Added complete edit/delete functionality with proper admin-only access control
- **Enhanced User Permission System**: Implemented permission-based navigation filtering throughout templates
- **Fixed QC Dashboard**: Added missing qc_approved_at field to GRPODocument model to resolve dashboard errors
- **Enhanced Picklist module**: Fixed ItemCode display issue in Pick List Items table
- Updated template to show ItemCode instead of OrderEntry number for better user experience
- Added ItemDescription and Customer details in enhanced picklist lines
- Improved bin allocation display to show warehouse details even when no bin allocations exist
- Confirmed picklist enhancement displays ItemCode by matching OrderEntry to Sales Order DocEntry and OrderRowID to LineNum
- **Enhanced InventoryTransferRequest module**: Added LineStatus checking to conditionally display "Add Remaining" buttons
- Updated template to hide "Add Remaining" button when LineStatus is "bost_Close" and show proper status indicators
- Added Status column to InventoryTransferRequest line items table displaying Open/Closed status with appropriate badges
- Enhanced transfer creation logic to properly track and log open vs closed line items
- **Fixed Dashboard Recent Activity**: Replaced hardcoded sample data with live database queries showing real GRPO, transfers, pick lists, and inventory counts
- **Fixed User Management Role-based Access**: Updated permission checking to properly allow admin role users to access user management functions
- **Enhanced Admin User**: Updated admin user permissions to include all necessary access rights
- **Updated MySQL migration**: Ensured all database changes are reflected in the comprehensive migration file
- **2025-08-23**: Serial Number Transfer Module Enhancements
- **Fixed Duplicate Line Item Issue**: Enhanced duplicate prevention logic with case-insensitive matching and trimming
- **Resolved Modal Freezing Issue**: Improved JavaScript event listeners and rendering to prevent UI freezing
- **QC Workflow Correction**: Disabled direct QC approval/rejection from serial transfer screen, redirected to QC Dashboard
- **Database Migration**: Successfully migrated from MySQL to PostgreSQL for Replit cloud compatibility
- **Enhanced Error Handling**: Added better error messages and user guidance for duplicate prevention
- **2025-08-24**: SAP B1 Integration Fixes for Inventory Transfers
- **Fixed Import Issues**: Resolved `sap_b1` import error by adding global SAP integration instance
- **Enhanced DocNum Validation**: Added validation to check if SAP B1 transfer requests are in "bost_Open" status before processing
- **Improved Warehouse Display**: Enhanced warehouse mapping in inventory transfer detail view with better visual indicators
- **Fixed QC Approval SAP Posting**: Added proper SAP B1 integration for inventory transfer posting after QC approval
- **Updated Inventory Transfer Creation**: Added comprehensive SAP B1 validation during transfer creation process
- **Fixed SAP B1 Method Call Error**: Corrected `create_stock_transfer` to `create_inventory_transfer` method call in QC approval posting
- **Enhanced Serial Number Duplicate Detection**: Added visual highlighting of duplicate serial numbers instead of automatic removal
- **Improved Serial Number UX**: Duplicate serials now show warning with visual indicators, allowing user review before submission
- **Enhanced Duplicate Prevention**: Added comprehensive duplicate checking at both frontend validation and backend processing levels
- **Enhanced Duplicate Management**: Modified system to allow duplicate serial numbers to be added for individual user review and deletion
- **Removed Unique Constraint**: Temporarily removed database unique constraint to enable user management of duplicate serial numbers
- **Improved User Control**: Users can now see all duplicate entries in serial numbers modal and selectively delete unwanted duplicates
- **2025-08-26**: Serial Item Transfer Module Implementation
- **New Module Created**: Built completely separate Serial Item Transfer module with models (SerialItemTransfer, SerialItemTransferItem)
- **SAP B1 Integration**: Integrated specific SAP B1 API endpoint (https://192.168.0.126:50000/b1s/v1/SQLQueries('Item_Validation')/List) for serial number validation
- **Auto-Population Feature**: Serial numbers are validated against SAP B1 and automatically populate ItemCode and ItemDescription
- **Complete Web Interface**: Created create, list, and detail views with full CRUD operations
- **User Permissions**: Added "serial_item_transfer" permission to user management system
- **Navigation Integration**: Added Serial Item Transfer menu item with proper role-based access control
- **MySQL Migration Updates**: Updated MySQL migration files to include new Serial Item Transfer tables for local database migration
- **Enhanced QC Dashboard**: Added Serial Item Transfer approval workflow with direct SAP B1 posting capability
- **SAP B1 Stock Transfer Posting**: Implemented direct API calls to SAP B1 StockTransfers endpoint for approved serial item transfers
- **Fixed SAP Integration**: Resolved method call errors by implementing direct SAP B1 API integration for stock transfer posting
- **Tab Key Navigation**: Enhanced serial number entry with tab key functionality for line-by-line input
- **Migration Complete**: Successfully migrated project from Replit Agent to standard Replit environment with PostgreSQL support
- **2025-08-26**: Fixed Serial Item Transfer SAP B1 Integration
- **Fixed Date Format Issue**: Resolved SAP B1 API error where ExpiryDate was being sent as string "None" instead of null values
- **Updated SAP Posting Logic**: Changed all date fields (ExpiryDate, ManufactureDate, ReceptionDate, WarrantyStart, WarrantyEnd) to use null instead of string "None"
- **Enhanced Error Handling**: Fixed SerialNumbers array formatting to prevent 400 errors when posting to SAP B1 StockTransfers endpoint
- **Validated Fix**: Serial Item Transfer module now properly posts to SAP B1 with correct date format expectations
- **2025-08-26**: Migration to Replit Environment Completed
- **PostgreSQL Database**: Successfully migrated from MySQL to PostgreSQL for Replit cloud compatibility
- **Performance Optimization**: Implemented batch serial number validation for processing 1000+ serial numbers efficiently
- **Batch Processing**: Added optimized batch validation functions that process serial numbers in chunks of 100 to avoid API timeouts
- **Enhanced SAP Integration**: Updated SAP B1 validation to support bulk queries reducing processing time from minutes to seconds for large datasets
- **Memory Optimization**: Implemented intelligent batch processing with progress tracking and memory management for enterprise-scale operations

## User Preferences
- None specified yet

## Credentials Configuration

### JSON File (Preferred Method)
The application now reads credentials from a JSON file instead of .env files. Place your credentials in one of these locations:
- **Windows**: `C:\tmp\sap_login\credential.json`
- **Linux/Replit**: `/tmp/sap_login/credential.json`

**credential.json format:**
```json
{
   "SAP_B1_SERVER":"https://192.168.0.109:50000",
   "SAP_B1_USERNAME":"manager",
   "SAP_B1_PASSWORD":"1422",
   "SAP_B1_COMPANY_DB":"EINV-TESTDB-LIVE-HUST",
   "MYSQL_HOST":"localhost",
   "MYSQL_PORT":"3306",
   "MYSQL_USER":"root",
   "MYSQL_PASSWORD":"root123",
   "MYSQL_DATABASE":"it_lobby",
   "DATABASE_URL":"mysql+pymysql://root:root123@localhost:3306/it_lobby",
   "SESSION_SECRET":"WMS-Secret-Key-20250915-Change-In-Production"
}
```

### Environment Variables (Fallback)
If the JSON file is not found, the application falls back to environment variables:
- `SESSION_SECRET`: Flask session secret key
- `DATABASE_URL`: Database connection URL
- `MYSQL_*`: MySQL configuration variables
- `SAP_B1_*`: SAP integration variables

## Security Notes
- Client/server separation maintained
- No hardcoded secrets in code
- Environment variable based configuration
- Proper password hashing implemented