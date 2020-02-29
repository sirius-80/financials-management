import decimal
import logging
import sqlite3
from sqlalchemy import create_engine, MetaData
from dependency_injector import providers
from domain import Blackboard

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
        logger.warning("Creating database connection")
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


class Database:
    def __init__(self):
        self.engine = create_engine("sqlite:///bank-sqlite3.db?"
                                    "check_same_thread=false")
        self.meta = MetaData()
        self.connection = self.engine.connect()

    def close(self):
        self.connection.close()

    def query(self, query, parameters=()):
        result = self.connection.execute(query, parameters)
        return result

    def query_one(self, query, parameters=()):
        result = self.connection.execute(query, parameters)
        return next(result)

    def get_engine(self):
        return self.engine


blackboard = Blackboard()


def init():
    logger.info("init %s", __file__)
    blackboard.database = providers.Singleton(Database)

