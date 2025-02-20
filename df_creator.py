import pandas as pd
from decimal_rounding import round_to_decimal


class DfCreator:
    def __init__(self, invoice_csv_headers, dropshipper_data):
        self.file_format_name = dropshipper_data["file_format_name"]

        # Creating a dataframe to store the invoice data
        self.invoice_file_df = pd.DataFrame(
            columns=invoice_csv_headers[self.file_format_name]
        )

    def populate_df(self, order):
        """Populates the dataframe with the order data."""
        try:

            if self.file_format_name == "default":
                row = {
                    "po_number": order["purchase_order_number"],
                    "invoice_number": order["order_id"],
                    "invoice_date": order["ship_date"],
                    "invoice_total_amount": order["subtotal"],
                    "invoice_subtotal_amount": round_to_decimal(
                        order["subtotal"] - order["tax"]
                    ),
                    "invoice_tax_amount": order["tax"],
                }
                for item in order["items"]:
                    sku, quantity, unit_cost = item
                    row["line_item_sku"] = sku
                    row["line_item_quantity"] = quantity
                    row["line_item_unit_cost"] = unit_cost

                    self.invoice_file_df = self.invoice_file_df._append(
                        row, ignore_index=True
                    )

            # If the file format is aag, the invoice data is stored in a different way
            elif self.file_format_name == "aag":
                row = {}
                for item in order["items"]:
                    sku, quantity, unit_cost = item
                    row = {
                        "Invoice Number": order["order_id"],
                        "SONumber": order["purchase_order_number"],
                        "Date": order["ship_date"],
                        "Customer": "auto_accessories_garage",
                        "CarrierName": "FEDEX_GROUND",
                        "TrackingNumber": order["tracking_number"],
                        "item": sku,
                        "qty": quantity,
                        "price": unit_cost * quantity,
                    }
                    self.invoice_file_df = self.invoice_file_df._append(
                        row, ignore_index=True
                    )
                tax_row = {
                    "Invoice Number": order["order_id"],
                    "SONumber": order["purchase_order_number"],
                    "Date": order["ship_date"],
                    "Customer": "auto_accessories_garage",
                    "CarrierName": "FEDEX_GROUND",
                    "TrackingNumber": order["tracking_number"],
                    "item": "Taxes",
                    "qty": 1,
                    "price": order["tax"],
                }
                self.invoice_file_df = self.invoice_file_df._append(
                    tax_row, ignore_index=True
                )
                shipping_row = {
                    "Invoice Number": order["order_id"],
                    "SONumber": order["purchase_order_number"],
                    "Date": order["ship_date"],
                    "Customer": "auto_accessories_garage",
                    "CarrierName": "FEDEX_GROUND",
                    "TrackingNumber": order["tracking_number"],
                    "item": "SHIPPING",
                    "qty": 1,
                    "price": order["shipping"],
                }
                self.invoice_file_df = self.invoice_file_df._append(
                    shipping_row, ignore_index=True
                )

            return True

        except Exception as e:
            print(f"Error while populating dataframe: {e}")

            return False

    def _order_invoice_matcher(self, order, invoice):
        order_items = {}
        order["subtotal"] = invoice.TotalAmt

        for line in invoice.Line:
            if line.Description == "Shipping":

                order["shipping"] = line.Amount

            elif line.Description == "Taxes":

                order["tax"] = line.Amount

            elif line.DetailType == "SalesItemLineDetail":

                # order_items[line.Description] = round(float(line.Amount), 2)
                order_items[line.Description] = line.Amount

        for i in range(len(order["items"])):
            sku, quantity, _ = order["items"][i]
            order["items"][i] = (sku, quantity, order_items[sku])

        return order
