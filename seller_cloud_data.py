from seller_cloud_api import SellerCloudAPI
from email_helper import send_email
import traceback


def get_sellercloud_data(ready_to_invoice_orders):
    """Gets the financial data from SellerCloud for the orders that are ready to be invoiced."""

    # Creating the SellerCloudAPI object to get the order data
    sc_api = SellerCloudAPI()

    # Iterating over the dropshippers NOTE: Using a copy of the ready_to_invoice_orders.items to remove any dropshipper that has no orders
    for dropshipper_key, dropshipper_data in list(ready_to_invoice_orders.items()):

        # Iterating over the orders to get the order data from SellerCloud NOTE: Using a copy of the orders to remove any order that has issues
        orders_copy = dropshipper_data["orders"].copy()
        for order in orders_copy:
            order_index = dropshipper_data["orders"].index(order)
            try:
                # Getting the order data from SellerCloud
                response = sc_api.execute(
                    {"url_args": {"order_id": order["sellercloud_order_id"]}},
                    "GET_ORDERS",
                )
                if response.status_code == 200:
                    sellercloud_order = response.json()
                    # Adding the financial data at the order level
                    order["tax"] = sellercloud_order["TotalInfo"]["Tax"]
                    order["subtotal"] = sellercloud_order["TotalInfo"]["GrandTotal"]
                    # Adding the financial data at the item level
                    for item in order["items"]:
                        # Keeping the original item data to be able to update the price later
                        item_index = order["items"].index(item)
                        sku, quantity = item
                        for product in sellercloud_order["OrderItems"]:
                            if product["ProductIDOriginal"] == sku:
                                item = (sku, quantity, product["LineTotal"] / quantity)
                                order["items"][item_index] = item
                                break
                        # If no price was added to the item, the order is removed from the list
                        if len(item) != 3:
                            print(f"Item {sku} not found in SellerCloud")
                            send_email(
                                f"Item {sku} on order {order['purchase_order_number']} was not found in SellerCloud",
                                "There is a missmatch on the skus the order has in the database and the ones it has in SellerCloud. No invoice was created.",
                            )
                            dropshipper_data["orders"].pop(order_index)
                            break
                # If the order was not found, the order is removed from the list
                else:
                    print(
                        f"Order {order['purchase_order_number']} not found in SellerCloud"
                    )
                    send_email(
                        f"Order {order['purchase_order_number']} not found in SellerCloud",
                        f"The API was not able to retrieve {order['purchase_order_number']} using the sellercloud_id {order['sellercloud_order_id']}. No invoice was created.",
                    )
                    dropshipper_data["orders"].pop(order_index)

            except Exception as e:
                print(f"Error: {e}")
                send_email(
                    f"Unable to get price data from SellerCloud for order {order['purchase_order_number']}",
                    f"An unexpected error occurred. No invoice was created.\nError: {e}\n\n{traceback.format_exc()}",
                )
                dropshipper_data["orders"].pop(order_index)

        # If there are no orders left for the dropshipper, the dropshipper is removed from the list
        if not dropshipper_data["orders"]:
            del ready_to_invoice_orders[dropshipper_key]

    return ready_to_invoice_orders
