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

## External Dependencies
- **SAP B1 Service Layer API**: For inventory management, goods receipt, pick lists, inventory transfers, and serial number validation.
- **PostgreSQL**: Primary database for production environments.
- **SQLite**: Local fallback database for development and initial setup.
- **Gunicorn**: Production web server for Flask application deployment.
- **Flask-Login**: For user authentication and session management.