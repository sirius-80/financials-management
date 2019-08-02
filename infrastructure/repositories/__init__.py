import logging
import sqlite3

logger = logging.getLogger(__name__)


class DatabaseSqlite3:
    def __init__(self):
        self.connection = sqlite3.connect("bank-sqlite3.db")
        self.connection.row_factory = sqlite3.Row

    def close(self):
        self.connection.close()

    def query(self, sql, parameters=()):
        logger.debug("Executing query: '%s' with parameters %s", sql, parameters)
        cursor = self.connection.cursor()
        cursor.execute(sql, parameters)
        rows = cursor.fetchall()
        logger.debug("Database returned: %d results", len(rows))
        return rows

    def query_one(self, sql, parameters=()):
        cursor = self.connection.cursor()
        cursor.execute(sql, parameters)
        row = cursor.fetchone()
        return row


_database = DatabaseSqlite3()


def get_database():
    return _database
