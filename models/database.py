import mysql.connector
import config


class Database:
    """Handles every MySQL connection and query for Maddie's System.
    All queries use placeholders (%s), which protects against SQL injection."""

    def __init__(self):
        self._settings = {
            "host": config.DB_HOST,
            "user": config.DB_USER,
            "password": config.DB_PASSWORD,
            "database": config.DB_NAME,
        }

    def _connect(self):
        return mysql.connector.connect(**self._settings)

    def fetch_one(self, query, params=None):
        """Return a single row as a dictionary, or None."""
        conn = self._connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            conn.close()

    def fetch_all(self, query, params=None):
        """Return a list of rows as dictionaries."""
        conn = self._connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            conn.close()

    def execute(self, query, params=None):
        """Run an INSERT, UPDATE, or DELETE. Returns the new row's id."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()