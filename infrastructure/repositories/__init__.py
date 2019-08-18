import decimal
import logging
import sqlite3

logger = logging.getLogger(__name__)


def _adapt_from_decimal(d):
    return str(d)


def _convert_to_decimal(s):
    return decimal.Decimal(s.decode('utf-8'))


sqlite3.register_adapter(decimal.Decimal, _adapt_from_decimal)
sqlite3.register_converter("decimal", _convert_to_decimal)
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("boolean", lambda v: bool(int(v)))


class DatabaseSqlite3:
    def __init__(self):
        self.connection = sqlite3.connect("bank-sqlite3.db",
                                          detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
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
