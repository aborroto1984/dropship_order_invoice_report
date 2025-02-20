from exampple_db import ExampleDb
from invoice import QbInvoice
from quick_books_db import QuickBooksDb
from email_helper import send_email
from seller_cloud_data import get_sellercloud_data
from file_handler import FileHandler
from df_creator import DfCreator
from ftp import FTPManager
import traceback
from tqdm import tqdm
from datetime import datetime, timedelta


def main():
    try:
        # Gettting invoice ready orders that have tracking numbers and
        # creating an object with the orders grouped by dropshipper
        ex_db = ExampleDb()
        invoice_csv_headers = ex_db.get_invoice_csv_headers()
        vendor_mappping = ex_db.get_vendor_mapping()

        ready_to_invoice_orders = ex_db.get_invoice_ready_orders()

        # Getting the financial data from SellerCloud
        ready_to_invoice_orders = get_sellercloud_data(ready_to_invoice_orders)

        if not ready_to_invoice_orders:
            print("There are no orders ready to be invoiced")
            send_email(
                "SellerCloud invoicing ran successfully",
                "There are not orders to invoice.",
            )
            ex_db.close()
            return

        # Creating the quickbooks api that takes care of making the invoice and sending it
        qb_db = QuickBooksDb()
        current_refresh_token = qb_db.get_refresh_token()
        api = QbInvoice(current_refresh_token)

        # Auto refresfing invoice token
        if api.client.refresh_token != current_refresh_token:
            qb_db.update_refresh_token(api.client.refresh_token)

        # Placeholders
        orders_unable_to_invoice = {}
        orders_already_invoiced = {}
        pos_invoiced = []
        tmp_files_paths = []

        # Report date
        report_date = datetime.now()  # - timedelta(days=1)
        f_handler = FileHandler(report_date)

        for dropshipper_info, dropshipper_data in ready_to_invoice_orders.items():
            # Getting the dropshipper code and the folder name for the FTP server
            dropshipper_code, ftp_folder_name = dropshipper_info

            # Creating the dataframe that will be used to create the invoice csv file
            df_creator = DfCreator(invoice_csv_headers, dropshipper_data)

            for order in tqdm(
                dropshipper_data["orders"],
                desc=f"Creating invoices for {dropshipper_code}",
            ):
                # Checking if the order has already been invoiced
                if not api.check_exist(order["order_id"]):
                    # Creating new invoice
                    invoice = api.create_invoice(order, vendor_mappping)

                    # If the invoice is None, it means that there was an error
                    if not invoice:
                        orders_unable_to_invoice.setdefault(
                            dropshipper_code, []
                        ).append(order["purchase_order_number"])
                    # If the invoice is not None, it means that the invoice was created successfully
                    else:
                        pos_invoiced.append(
                            (order),
                        )
                        # Adding the invoice data to the dataframe
                        in_file = df_creator.populate_df(order)

                        if not in_file:
                            # If the invoice was not created correctly, it is deleted
                            just_created_invoice = api.check_exist(order["order_id"])
                            api.delete_invoice(just_created_invoice)
                            orders_unable_to_invoice.setdefault(
                                dropshipper_code, []
                            ).append(order["purchase_order_number"])

                # If the order has already been invoiced, it is added to the orders_already_invoiced dictionary
                else:
                    orders_already_invoiced.setdefault(dropshipper_code, []).append(
                        order["purchase_order_number"]
                    )
                    # Adding the order to the pos_invoiced list so that the is_invoiced status can be updated
                    pos_invoiced.append(
                        (order),
                    )

            # Creating the tmp folder and saving the invoice data to a csv file
            file_path = f_handler.save_data_to_file(
                df_creator.invoice_file_df, ftp_folder_name
            )
            if file_path:
                tmp_files_paths.append(file_path)
        # Uploading the files to the FTP server
        if tmp_files_paths:
            ftp = FTPManager()
            ftp.upload_files(tmp_files_paths)

        if orders_unable_to_invoice or orders_already_invoiced:
            # Sending an email to notify of the orders that were unable to be invoiced
            send_error_report(orders_unable_to_invoice, orders_already_invoiced)

        if pos_invoiced:
            # Updating the is_invoiced status of the PurchaseOrders table
            ex_db.update_invoice_status(pos_invoiced)

        send_email(
            "SellerCloud invoicing ran successfully",
            f"Dont forget to run the test.\n\t{pos_invoiced}",
        )

        ex_db.close()
        qb_db.close()

    except Exception as e:
        print(f"There was an error: {e}")
        send_email("An Error Occurred", f"Error: {e}\n\n{traceback.format_exc()}")
        raise e


if __name__ == "__main__":
    main()
