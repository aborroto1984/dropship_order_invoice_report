# Order Invoicing and Processing System

This project automates order processing, invoice generation, and data management using multiple integrations, including FTP servers, SellerCloud, and QuickBooks.

## Features
- Fetches and processes orders from SellerCloud.
- Validates order files and invoice data.
- Rounds decimal values for financial accuracy.
- Creates invoices and sends them to QuickBooks.
- Uploads processed files to an FTP server.
- Stores and retrieves order data from an SQL database.
- Sends email notifications for errors and important updates.

## Project Structure
project_root/ ├── config.py # Configuration file for database, API, and email credentials ├── decimal_rounding.py # Handles rounding of decimal values ├── df_creator.py # Handles invoice data structuring ├── email_helper.py # Sends email notifications ├── exampple_db.py # Manages database interactions for invoicing ├── file_handler.py # Handles file creation and storage ├── ftp.py # Manages FTP file uploads ├── invoice.py # Handles invoice creation via QuickBooks API ├── main.py # Main script orchestrating the invoicing process ├── quick_books_db.py # Manages QuickBooks API tokens ├── seller_cloud_api.py # Interfaces with SellerCloud API ├── seller_cloud_data.py # Fetches and processes SellerCloud order data

## Installation & Setup

### 1. Clone the Repository

git clone https://github.com/your-repo/order-processing.git
cd order-processing

### 2. Install Dependencies
Ensure you have Python 3 installed, then install dependencies:
pip install -r requirements.txt

### 3. Configure the System
Modify config.py with your database, FTP, and API credentials.

## Example database configuration:

db_config = {
    "ExampleDb": {
        "server": "your.database.windows.net",
        "database": "YourDB",
        "username": "your_user",
        "password": "your_password",
        "driver": "{ODBC Driver 17 for SQL Server}",
    },
}

## Example email configuration:

SENDER_EMAIL = "your_email@example.com"
SENDER_PASSWORD = "your_email_password"

## Usage

Run the main script to start the process:
python main.py

## How It Works

- Fetches order data from SellerCloud.
- Validates and processes invoice data.
- Rounds decimal values for financial accuracy.
- Generates invoices and sends them to QuickBooks.
- Uploads processed invoice files to an FTP server.
- Updates the database with invoice details.
- Sends email notifications for errors or missing data.

# Tech Stack

- Python 3
- Azure SQL Database (pyodbc)
- FTP File Handling (ftplib)
- SellerCloud API Integration
- QuickBooks API Integration
- Email Notifications (smtplib)
- Pandas for data handling
- Decimal rounding for financial accuracy

# Troubleshooting

- If you encounter database connection issues, ensure ODBC Driver 17 is installed.
- If emails fail to send, ensure your SMTP settings allow external authentication.
- Verify SellerCloud and QuickBooks credentials if API requests fail.