import pyodbc
from config import create_connection_string, db_config
from decimal_rounding import round_to_decimal
from datetime import datetime
from tqdm import tqdm


class ExampleDb:
    def __init__(self):
        try:
            self.conn = pyodbc.connect(create_connection_string(db_config["ExampleDb"]))
            self.cursor = self.conn.cursor()
        except pyodbc.Error as e:
            print(f"Error establishing connection to the ExampleDb database: {e}")
            raise

    def get_invoice_ready_orders(self):
        """Gets all the untracked orders from the ExampleDb database."""
        try:
            self.cursor.execute(
                """
                SELECT   
                    po.id,     
                    po.purchase_order_number,
                    po.sellercloud_order_id,
                    po.shipping_cost,
                    po.tracking_number,
                    po.tracking_date,
                    po.city,
                    po.zip,
                    po.address,
                    s.code AS state,
                    c.two_letter_code AS country,
                    d.code,
                    d.name,
                    d.ftp_folder_name,
                    ff.name AS file_format_name
                FROM PurchaseOrders po
                JOIN Dropshippers d ON po.dropshipper_id = d.id
                JOIN States s ON po.state = s.id
                JOIN Countries c ON po.country = c.id
                JOIN DropshipperFileFormats dff ON dff.dropshipper_id = d.id
                JOIN FileFormats ff ON ff.id = dff.format_id
                WHERE po.tracking_number IS NOT NULL AND ff.type = 'invoice' AND po.is_invoiced = 0
                """
            )

            rows = self.cursor.fetchall()

            dropshippers_untracked_orders = {}

            for row in tqdm(rows, desc="Getting ready to invoice orders"):
                # Creating a tuple to identify the dropshipper
                dropshipper_info = (row.code, row.ftp_folder_name)
                items = self._get_invoice_ready_order_items(row.id)

                order = {
                    "items": items,
                    "purchase_order_number": row.purchase_order_number,
                    "sellercloud_order_id": row.sellercloud_order_id,
                    "tax": "",  # Because is null
                    "shipping": round_to_decimal(row.shipping_cost),
                    "subtotal": "",  # Because is null
                    "code": row.code,
                    "tracking_number": row.tracking_number,
                    "ship_date": row.tracking_date.strftime("%Y/%m/%d"),
                    "city": row.city,
                    "state": row.state,
                    "country": row.country,
                    "postal_code": row.zip,
                    "address": row.address,
                    "dropshipper_name": row.name,
                }
                # Making sure that the dropshipper code is included in the order id
                code_length = len(row.code)
                if row.purchase_order_number[:code_length] == row.code:
                    order["order_id"] = row.purchase_order_number
                else:
                    order["order_id"] = row.code + row.purchase_order_number

                # Adding the order to the dictionary using the dropshipper info as the key
                if dropshippers_untracked_orders.get(dropshipper_info):
                    dropshippers_untracked_orders[dropshipper_info]["orders"].append(
                        order
                    )

                else:
                    dropshippers_untracked_orders[dropshipper_info] = {
                        "orders": [order],
                        # The file format name is used to determine the csv headers
                        "file_format_name": row.file_format_name,
                    }

            return dropshippers_untracked_orders

        except Exception as e:
            print(f"Error while storing purchase orders: {e}")
            raise

    def _get_invoice_ready_order_items(self, id):
        """Gets all the untracked order items from the ExampleDb database."""
        try:
            self.cursor.execute(
                """
                SELECT
                    poi.sku,
                    poi.quantity
                FROM PurchaseOrderItems poi
                WHERE poi.purchase_order_id = ?
                """,
                id,
            )
            rows = self.cursor.fetchall()

            untracked_order_items = [(row.sku, row.quantity) for row in rows]

            # return untracked_order_items, items_price_total
            return untracked_order_items

        except Exception as e:
            print(f"Error while storing purchase order items: {e}")
            raise

    def get_vendor_mapping(self):
        """Gets the vendor mapping from the ExampleDb database"""
        try:
            self.cursor.execute(
                """
                SELECT
                    name,
                    ship_method,
                    invoice_email,
                    quickbook_id
                FROM Dropshippers WHERE code != 'ABS'
                """
            )
            rows = self.cursor.fetchall()
            vendor_mapping = {}
            for row in rows:
                vendor_mapping[row.name] = {
                    "ship_method": row.ship_method,
                    "email": row.invoice_email,
                    "customer_id": row.quickbook_id,
                }

            return vendor_mapping

        except Exception as e:
            print(f"Error while getting vendor mapping: {e}")
            raise

    def get_invoice_csv_headers(self):
        """Gets the csv headers for the invoice files."""
        try:
            self.cursor.execute(
                """
                SELECT 
                    f.name AS file_format_name,
                    STRING_AGG(fd.header_name, ', ') AS header_names
                FROM fileformats f 
                JOIN fileformatdetails fd ON fd.format_id = f.id
                WHERE f.type = 'invoice'
                GROUP BY f.name
                ORDER BY f.name;
                """
            )
            rows = self.cursor.fetchall()
            headers = {
                row.file_format_name: row.header_names.split(", ") for row in rows
            }
            return headers
        except Exception as e:
            print(f"Error while getting csv headers: {e}")
            raise

    def update_invoice_status(self, pos_invoiced):
        """Updates the invoice status of the given purchase order number."""
        po_update_data = []
        items_update_data = []

        for order in pos_invoiced:
            subtotal = 0
            for item in order["items"]:
                sku, quantity, price = item
                subtotal += price
                items_update_data.append((price, order["purchase_order_number"], sku))
            po_update_data.append(
                (
                    subtotal,
                    order["shipping"],
                    order["tax"],
                    order["subtotal"],
                    datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    order["purchase_order_number"],
                )
            )

        try:
            self.cursor.executemany(
                """
                UPDATE PurchaseOrders
                SET 
                subtotal = ?,
                shipping_cost = ?,
                tax = ?,
                total = ?,
                is_invoiced = 1,
                invoiced_date = ?
                WHERE purchase_order_number = ?
                """,
                po_update_data,
            )

            self.cursor.executemany(
                """
                UPDATE PurchaseOrderItems
                SET 
                price = ?
                WHERE purchase_order_id = (SELECT id FROM PurchaseOrders WHERE purchase_order_number = ?) AND sku = ?
                """,
                items_update_data,
            )

            self.conn.commit()
        except Exception as e:
            print(f"Error while updating invoice status: {e}")
            raise

    def close(self):
        self.conn.close()
