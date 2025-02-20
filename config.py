db_config = {
    "ExampleDb": {
        "server": "example.database.windows.net",
        "database": "ExampleDb",
        "username": "example",
        "password": "example",
        "driver": "{ODBC Driver 17 for SQL Server}",
        "port": 1433,  # Default port for SQL Server
    },
    "QuickBooks_ExampleDb": {
        "server": "example.database.windows.net",
        "database": "QuickBooks_ExampleDb",
        "username": "example",
        "password": "example",
        "driver": "{ODBC Driver 17 for SQL Server}",
        "port": 1433,  # Default port for SQL Server
    },
}


def create_connection_string(server_config):
    return (
        f"DRIVER={server_config['driver']};"
        f"SERVER={server_config['server']};"
        f"PORT={server_config["port"]};DATABASE={server_config['database']};"
        f"UID={server_config['username']};"
        f"PWD={server_config['password']}"
    )


ftp_server = {
    "server": "ftp.example.com",
    "username": "example",
    "password": "password",
}


client_data = {
    "client_id": "example_client_id",
    "client_secret": "example_client_secret",
    "redirect_uri": "example_redirect_uri",
    "environment": "sandbox",
    "realm_id": "example_realm_id",
    "access_token": "example_access_token",
}


sellercloud_credentials = {
    "Username": "username",
    "Password": "password",
}

sellercloud_base_url = "https://example_company.api.sellercloud.us/rest/api/"
sellercloud_endpoints = {
    "GET_TOKEN": {
        "type": "post",
        "url": sellercloud_base_url + "token",
        "endpoint_error_message": "while getting SellerCoud API access token: ",
        "success_message": "Got SellerCloud API access token successfully!",
    },
    "GET_ORDERS": {
        "type": "get",
        "url": sellercloud_base_url + "Orders/{order_id}",
        "endpoint_error_message": "while getting order from SellerCloud: ",
        "success_message": "Got an order successfully!",
    },
}


SENDER_EMAIL = "sender_email@domain.com"
SENDER_PASSWORD = "sender_password"
RECIPIENT_EMAILS = [
    "recipient_email_1@domain.com",
    "recipient_email_2@domain.com",
]  # List of emails to send the report
