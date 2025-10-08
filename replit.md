# Warehouse Management System (WMS)

## Overview
A Flask-based Warehouse Management System (WMS) designed to streamline inventory operations. It features seamless integration with SAP for core functionalities like barcode scanning, goods receipt, pick list generation, and inventory transfers. The system aims to enhance efficiency, accuracy, and control over warehouse logistics.

## User Preferences
None specified yet

## System Architecture
The system is built on a Flask web application backend, utilizing Jinja2 for server-side rendering of the frontend. A key architectural decision is the deep integration with the SAP B1 Service Layer API for all critical warehouse operations, ensuring data consistency and real-time updates. For database management, SQLite is used as a fallback with automatic initialization, while the primary deployment targets PostgreSQL for cloud compatibility. User authentication is handled via Flask-Login with robust role-based access control. The application is designed for production deployment using Gunicorn with an autoscale configuration. Key features include comprehensive user authentication, GRPO management, inventory transfer requests, pick list management, barcode scanning, branch management, and a quality control dashboard. UI/UX focuses on intuitive workflows for managing inventory, including serial number transfers and real-time validation against SAP B1.

## External Dependencies
- **SAP B1 Service Layer API**: For inventory management, goods receipt, pick lists, inventory transfers, and serial number validation.
- **PostgreSQL**: Primary database for production environments.
- **SQLite**: Local fallback database for development and initial setup.
- **Gunicorn**: Production web server for Flask application deployment.
- **Flask-Login**: For user authentication and session management.