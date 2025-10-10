# Warehouse Management System (WMS)

## Overview
A Flask-based Warehouse Management System (WMS) designed to streamline inventory operations. It features seamless integration with SAP for core functionalities like barcode scanning, goods receipt, pick list generation, and inventory transfers. The system aims to enhance efficiency, accuracy, and control over warehouse logistics.

## User Preferences
None specified yet

## System Architecture
The system is built on a Flask web application backend, utilizing Jinja2 for server-side rendering of the frontend. A key architectural decision is the deep integration with the SAP B1 Service Layer API for all critical warehouse operations, ensuring data consistency and real-time updates. For database management, SQLite is used as a fallback with automatic initialization, while the primary deployment targets PostgreSQL for cloud compatibility. User authentication is handled via Flask-Login with robust role-based access control. The application is designed for production deployment using Gunicorn with an autoscale configuration. Key features include comprehensive user authentication, GRPO management, inventory transfer requests, pick list management, barcode scanning, branch management, and a quality control dashboard. UI/UX focuses on intuitive workflows for managing inventory, including serial number transfers and real-time validation against SAP B1.

### Inventory Transfer Module Enhancement (Oct 2025)
The Inventory Transfer module now includes enhanced document series selection:
- **Document Series Dropdown**: Uses SAP B1 SQLQueries('Get_INVT_Series')/List to retrieve available series
- **DocEntry Retrieval**: Automatically fetches DocEntry using series and DocNum via SQLQueries('Get_INVT_DocEntry')/List
- **Document Validation**: Only allows "bost_Open" status documents to be processed (closed documents are rejected)
- **Auto-population**: Fetches complete document details including header and line items from InventoryTransferRequests endpoint
- **Template Location**: Uses templates in `/templates/` directory for inventory transfer UI (not module directory)

### User Management Module Improvements (Oct 9, 2025)
Enhanced user management with bug fixes, security improvements, and new self-service profile features:
- **Bug Fix**: Corrected user deactivation issue in multiple templates
  - Fixed `templates/user_management.html`: Changed `is_active` to `user.active`
  - Fixed `templates/edit_user.html`: Changed `user.is_active` to `user.active` (Oct 9, 2025)
  - Database schema already used correct `active` field
- **Security**: Removed delete user functionality - users can only be deactivated (preserves audit trail)
- **User Profile System**: Added self-service profile management for all users
  - `/profile` route: View own profile
  - `/profile/edit` route: Edit own profile (name, email, password)
  - Navigation updated with "My Profile" link in user dropdown
- **Access Control**: Admin retains full user management; regular users can only view/edit their own profile
- **Error Handling**: Comprehensive validation for profile updates including duplicate email detection and database error recovery
- **No Schema Changes**: All improvements are code-only updates with no database migrations required

### Camera Scanning - Environment Differences (Oct 9, 2025)
Camera/barcode scanning modules work correctly in Replit but require specific configuration for local development:
- **Issue**: Browsers require HTTPS or localhost for camera access (security policy)
- **Replit**: Works automatically (uses HTTPS by default)
- **Local Development Solutions**:
  - Use `localhost:5000` or `127.0.0.1:5000` (easiest)
  - Set up HTTPS with self-signed certificates or mkcert
  - Use ngrok for remote testing with HTTPS
- **Affected Modules**: GRPO, Bin Scanning, Pick List, Inventory Transfer, Barcode Reprint
- **Documentation**: See `CAMERA_SCANNING_GUIDE.md` for detailed setup instructions
- **Production**: No changes needed (Replit deployments use HTTPS automatically)

### Inventory Counting Module Enhancement (Oct 10, 2025)
The Inventory Counting module now includes SAP B1 integration for document-based counting:
- **Document Series Dropdown**: Uses SAP B1 SQLQueries('Get_INVCNT_Series')/List to retrieve available series
- **DocEntry Retrieval**: Automatically fetches DocEntry using series and DocNum via SQLQueries('Get_INVCNT_DocEntry')/List
- **Document Validation**: Only allows "cdsOpen" status documents to be processed (closed documents are rejected)
- **Auto-population**: Fetches complete document details including counting lines from InventoryCountings endpoint
- **Two Modes Available**:
  - SAP Counting (`/inventory_counting_sap`): Document-based counting with SAP B1 integration
  - Local Counting (`/inventory_counting`): Local count tasks and quick counting
- **Navigation**: Counting dropdown menu provides access to both modes
- **Template Location**: Uses templates in `/templates/` directory for inventory counting UI
- **No Schema Changes**: All improvements are code-only updates with no database migrations required

## External Dependencies
- **SAP B1 Service Layer API**: For inventory management, goods receipt, pick lists, inventory transfers, and serial number validation.
- **PostgreSQL**: Primary database for production environments.
- **SQLite**: Local fallback database for development and initial setup.
- **Gunicorn**: Production web server for Flask application deployment.
- **Flask-Login**: For user authentication and session management.