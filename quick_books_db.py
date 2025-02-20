import pyodbc
from config import create_connection_string, db_config


class QuickBooksDb:
    def __init__(self):
        self.conn = pyodbc.connect(
            create_connection_string(db_config["QuickBooks_ExampleDb"])
        )
        self.cursor = self.conn.cursor()

    def get_refresh_token(self):
        self.cursor.execute("SELECT TOP 1 (refresh_token) FROM keys ORDER BY ID DESC")
        return self.cursor.fetchone()[0]

    def update_refresh_token(self, refresh_token):
        conn = pyodbc.connect(
            create_connection_string(db_config["QuickBooks_ExampleDb"])
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO keys (refresh_token) VALUES (?)", refresh_token)
        conn.commit()
        return True

    def close(self):
        self.conn.close()
