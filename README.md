# Warehouse Management System

A mobile-optimized web application built with Python Flask for managing a warehouse. The system supports product and box management using QR codes for creation, scanning, and tracking. It utilizes a persistent database (SQLite via Flask-SQLAlchemy) and offers both file upload and camera-based QR code scanning.

## Features

- **Product Management**
  - Create new products with a normalized name and a location (shelf number and level).
  - Generate QR codes for each product.
  - Scan product QR codes via file upload or directly using the device's camera.
  - Delete products from the warehouse.

- **Box (Container) Management**
  - Create new boxes with an optional name.
  - Generate QR codes for boxes with the box name (if provided) displayed above the QR code.
  - Scan box QR codes via file upload or camera.
  - Add scanned products to a box and remove products from boxes.
  - Delete boxes from the warehouse.

- **User Interface**
  - Responsive design optimized for mobile devices.
  - Clean, modern UI with a fixed header menu and organized grid layout for warehouse view.
  - Modal popups for displaying QR codes with options to download.
  - Unified scanning pages for both products and boxes, offering upload and camera-based scanning in a single interface.

## Technologies Used

- **Backend:** Python, Flask, Flask-SQLAlchemy
- **QR Code Generation:** [qrcode](https://pypi.org/project/qrcode/) with Pillow
- **QR Code Scanning:** [pyzbar](https://pypi.org/project/pyzbar/) and [html5-qrcode](https://github.com/mebjas/html5-qrcode)
- **Frontend:** HTML, CSS, JavaScript (with responsive design)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/warehouse-management.git
   cd warehouse-management
