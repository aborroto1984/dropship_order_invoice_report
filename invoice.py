from config import client_data
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.objects import (
    Invoice,
    SalesItemLineDetail,
    SalesItemLine,
    Item,
    Term,
    Class,
    Customer,
)
from datetime import datetime
from quickbooks.objects.base import Ref, Address, EmailAddress


def format_date(date_str, input_format="%m/%d/%Y", output_format="%Y-%m-%d"):
    return datetime.strptime(date_str, input_format).strftime(output_format)


class QbInvoice:
    def __init__(self, current_refresh_token):
        self.auth_client = AuthClient(
            client_id=client_data["client_id"],
            client_secret=client_data["client_secret"],
            environment=client_data["environment"],
            redirect_uri=client_data["redirect_uri"],
        )
        self.client = QuickBooks(
            auth_client=self.auth_client,
            refresh_token=current_refresh_token,
            company_id=client_data["realm_id"],
        )

    def _create_sales_item_line(
        self, sku, quantity, unit_cost, item_ref, class_ref, date
    ):
        line_detail = SalesItemLineDetail()
        line_detail.ServiceDate = date
        line_detail.UnitPrice = unit_cost
        line_detail.Qty = quantity
        line_detail.ItemRef = item_ref
        line_detail.ClassRef = class_ref

        line = SalesItemLine()
        line.Amount = str(float(unit_cost) * quantity)
        line.DetailType = "SalesItemLineDetail"
        line.Description = sku
        line.SalesItemLineDetail = line_detail

        return line

    def _create_tax_line(self, unit_cost, tax_ref, class_ref, date):
        line_detail = SalesItemLineDetail()
        line_detail.ServiceDate = date
        line_detail.UnitPrice = unit_cost
        line_detail.Qty = 1
        line_detail.ItemRef = tax_ref
        line_detail.ClassRef = class_ref

        line = SalesItemLine()
        line.Amount = unit_cost * 1
        line.DetailType = "SalesItemLineDetail"
        line.Description = "Taxes"
        line.SalesItemLineDetail = line_detail

        return line

    def _create_shipping_line(self, unit_cost, shipping_ref, class_ref, date):
        line_detail = SalesItemLineDetail()
        line_detail.ServiceDate = date
        line_detail.UnitPrice = unit_cost
        line_detail.Qty = 1
        line_detail.ItemRef = shipping_ref
        line_detail.ClassRef = class_ref
        line = SalesItemLine()
        line.Amount = unit_cost
        line.DetailType = "SalesItemLineDetail"
        line.Description = "Shipping"
        line.SalesItemLineDetail = line_detail

        return line

    def _prepare_invoice(
        self, row, line_items, customer_ref, term_ref, ship_method_ref, vendor_mappping
    ):
        invoice = Invoice()
        invoice.CustomerRef = customer_ref
        invoice.SalesTermRef = term_ref
        invoice.TrackingNum = row["tracking_number"]
        invoice.ShipDate = row["ship_date"]
        invoice.Line = line_items
        invoice.TxnDate = row["ship_date"]
        invoice.DocNumber = row["order_id"]
        invoice.BillEmail = EmailAddress()
        invoice.BillEmail.Address = vendor_mappping[row["dropshipper_name"]]["email"]

        invoice.ShipMethodRef = ship_method_ref
        invoice.ShipAddr = Address()
        invoice.ShipAddr.City = row["city"]
        invoice.ShipAddr.CountrySubDivisionCode = row["state"]
        invoice.ShipAddr.Country = row["country"]
        invoice.ShipAddr.PostalCode = row["postal_code"]
        invoice.ShipAddr.Line1 = row["address"]

        return invoice

    def create_invoice(self, row, vendor_mappping):
        items = row["items"]
        date = row["ship_date"]

        item_ref = Item.get(2, qb=self.client).to_ref()
        tax_ref = Item.get(24, qb=self.client).to_ref()
        shipping_ref = Item.get(23, qb=self.client).to_ref()
        class_ref = Class.get(1111, qb=self.client).to_ref()  # Class id placeholder

        line_items = []

        for item in items:
            sku, quantity, unit_cost = item

            sales_item_line = self._create_sales_item_line(
                sku, quantity, unit_cost, item_ref, class_ref, date
            )
            line_items.append(sales_item_line)

        # adding the tax line
        line_items.append(self._create_tax_line(row["tax"], tax_ref, class_ref, date))
        line_items.append(
            self._create_shipping_line(row["shipping"], shipping_ref, class_ref, date)
        )

        ship_method_ref = Ref()
        ship_method_ref.value = vendor_mappping[row["dropshipper_name"]]["ship_method"]
        ship_method_ref.name = vendor_mappping[row["dropshipper_name"]]["ship_method"]

        customer_id = vendor_mappping[row["dropshipper_name"]]["customer_id"]
        customer_ref = Customer.get(customer_id, qb=self.client).to_ref()
        term_ref = Term.get(4, qb=self.client).to_ref()
        try:
            invoice = self._prepare_invoice(
                row,
                line_items,
                customer_ref,
                term_ref,
                ship_method_ref,
                vendor_mappping,
            )
        except Exception as e:
            print(e)
            return False
        try:
            invoice.save(qb=self.client)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def check_exist(self, invoice_number):
        try:
            invoice = Invoice.filter(DocNumber=invoice_number, qb=self.client)[0]
            return invoice
        except IndexError:
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_invoice(self, invoice: Invoice):
        try:
            invoice.delete(qb=self.client)
            return True

        except IndexError:
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def close(self):
        self.client.close()
