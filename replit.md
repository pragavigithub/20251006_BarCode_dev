# Warehouse Management System (WMS)

## Overview
A Flask-based Warehouse Management System (WMS) designed to streamline inventory operations. It features seamless integration with SAP for core functionalities like barcode scanning, goods receipt, pick list generation, and inventory transfers. The system aims to enhance efficiency, accuracy, and control over warehouse logistics. The project envisions a future where warehouse operations are fully digitized, minimizing manual errors and maximizing throughput, potentially serving as a model for small to medium-sized enterprises.

## Recent Changes
*   **2025-10-17**: Disabled automatic SAP item code validation in GRPO "Add Item" functionality. Users can now enter item codes manually without triggering SAP validation alerts. All batch/serial fields are now available for manual entry by default, improving workflow flexibility when SAP validation is unavailable or unnecessary.
*   **2025-10-17**: Fixed Jinja2 template structure error in GRPO detail page (`grpo_detail.html`). Added missing `{% endblock %}` tag to properly close the scripts block after JavaScript code. The QR modal is now correctly placed in the content block. Template now renders without "Unexpected end of template" errors.
*   **2025-10-17**: Fixed critical JavaScript rendering issue in GRPO detail page (`grpo_detail.html`). Resolved duplicate `{% endblock %}` template tag and escaped `</script>` tag within JavaScript template literal to prevent premature script termination. JavaScript code is now properly executed instead of being displayed as text on the page.
*   **2025-10-17**: Enhanced GRPO "Add Item to GRN" UI logic to properly hide batch number and expiration date fields when item is serial-managed. Updated JavaScript validation to target the entire batch/expiration row for consistent visibility toggling between batch and serial fields.
*   **2025-10-17**: Added barcode generation functionality for batch numbers in GRPO module. Batch-managed items now have a "Generate Barcode" button that creates QR codes with the format "BATCH:{itemCode}-{batchNumber}" and includes print functionality.

## User Preferences
*   Keep MySQL migration files updated when database schema changes occur

## System Architecture
The system is built on a Flask web application backend, utilizing Jinja2 for server-side rendering. A core architectural decision is the deep integration with the SAP B1 Service Layer API for all critical warehouse operations, ensuring data consistency and real-time updates. SQLite serves as a fallback database, while PostgreSQL is the primary target for cloud deployments. User authentication uses Flask-Login with robust role-based access control. The application is designed for production deployment using Gunicorn with autoscale capabilities.

**Key Features:**
*   **User Management:** Comprehensive authentication, role-based access, and self-service profile management. Deactivation replaces deletion for audit trails.
*   **GRPO Management:** Includes standard Goods Receipt PO processing with intelligent batch/serial field management and a new module for batch creation of multiple GRNs from multiple Purchase Orders via a 5-step workflow with SAP B1 integration.
    *   **Dynamic Batch/Serial Detection (NEW):** Automatically validates item codes against SAP B1 to determine if items are batch-managed or serial-managed, showing only relevant input fields
    *   **Serial Number Entry:** For serial-managed items, dynamically generates individual serial number inputs based on received quantity with automatic barcode generation
    *   **Batch Number Entry:** For batch-managed items, enables batch number selection with expiration date tracking
*   **Inventory Transfer:** Enhanced module for creating inventory transfer requests with document series selection and validation against SAP B1.
*   **Pick List Management:** Generation and processing of pick lists.
*   **Barcode Scanning:** Integrated camera-based scanning for various modules (GRPO, Bin Scanning, Pick List, Inventory Transfer, Barcode Reprint), requiring HTTPS for local development.
*   **Inventory Counting:** Supports both SAP document-based counting and local quick counting tasks.
*   **Branch Management:** Functionality for managing different warehouse branches.
*   **Quality Control Dashboard:** Provides oversight for quality processes.
*   **UI/UX:** Focuses on intuitive workflows for managing inventory, including serial number transfers and real-time validation against SAP B1.
*   **Database Migrations:** A comprehensive MySQL migration tracking system is in place for schema changes, complementing the primary PostgreSQL strategy.

**Technical Implementations:**
*   **SAP B1 Integration:** Utilizes a dedicated `SAPMultiGRNService` class for secure and robust communication with the SAP B1 Service Layer, including SSL/TLS verification. OData filtering is optimized for `CardCode` for reliability.
*   **Modular Design:** New features like Multi-GRN Creation are implemented as modular blueprints with their own templates and services.
*   **Frontend:** Jinja2 templating with JavaScript libraries like Select2 for enhanced UI components.
*   **Error Handling:** Comprehensive validation and error logging for API communications and user inputs.

## External Dependencies
*   **SAP B1 Service Layer API**: For all core inventory and document management functionalities (GRPO, pick lists, inventory transfers, serial numbers, business partners, inventory counts).
*   **PostgreSQL**: Primary relational database for production environments.
*   **SQLite**: Local relational database for development and initial setup.
*   **Gunicorn**: WSGI HTTP server for deploying the Flask application in production.
*   **Flask-Login**: Library for managing user sessions and authentication.