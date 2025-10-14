# Warehouse Management System (WMS)

## Overview
A Flask-based Warehouse Management System (WMS) designed to streamline inventory operations. It features seamless integration with SAP for core functionalities like barcode scanning, goods receipt, pick list generation, and inventory transfers. The system aims to enhance efficiency, accuracy, and control over warehouse logistics. The project envisions a future where warehouse operations are fully digitized, minimizing manual errors and maximizing throughput, potentially serving as a model for small to medium-sized enterprises.

## User Preferences
None specified yet

## System Architecture
The system is built on a Flask web application backend, utilizing Jinja2 for server-side rendering. A core architectural decision is the deep integration with the SAP B1 Service Layer API for all critical warehouse operations, ensuring data consistency and real-time updates. SQLite serves as a fallback database, while PostgreSQL is the primary target for cloud deployments. User authentication uses Flask-Login with robust role-based access control. The application is designed for production deployment using Gunicorn with autoscale capabilities.

**Key Features:**
*   **User Management:** Comprehensive authentication, role-based access, and self-service profile management. Deactivation replaces deletion for audit trails.
*   **GRPO Management:** Includes standard Goods Receipt PO processing and a new module for batch creation of multiple GRNs from multiple Purchase Orders via a 5-step workflow with SAP B1 integration.
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