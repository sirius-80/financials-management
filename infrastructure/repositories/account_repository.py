import decimal
import logging
import uuid

from account_management.domain.model.account import AccountRepository, Account, Transaction, AccountFactory, \
    AccountCreatedEvent, TransactionCreatedEvent
from infrastructure import publish_domain_events
from infrastructure.repositories import get_database, category_repository

logger = logging.getLogger(__name__)


class _AccountCache:
    def __init__(self, db):
        self.db = db
        self.accounts = {}
        self.transactions = {}

    def update_account(self, account):
        if account.id not in self.accounts.keys():
            self.accounts[account.id] = account
        assert self.accounts[account.id] is account
        return account

    def update_transaction(self, transaction):
        if transaction.id not in self.transactions.keys():
            self.transactions[transaction.id] = transaction
        assert self.transactions[transaction.id] is transaction

        stored_account = self.get_account_by_id(transaction.account.id)
        stored_account.transactions = [transaction if transaction.id == t.id else t
                                       for t in stored_account.transactions]

    def get_accounts(self):
        # logger.debug("Getting accounts from cache: %s (size=%d)", self.accounts, len(self.accounts))
        return self.accounts.values()

    def get_account_by_name(self, name):
        # logger.debug("Getting account with name %s from cache (%s)", name, self.accounts)
        cached = next(iter(a for a in self.accounts.values() if a.name == name), None)
        # logger.debug("Got from cache: %s", cached)
        return cached

    def get_account_by_id(self, id):
        if id in self.accounts.keys():
            return self.accounts[id]
        else:
            return None

    def get_transaction_by_id(self, id):
        if id in self.transactions.keys():
            return self.transactions[id]
        else:
            return None

    def init_cache(self):
        logger.info("Initializing cache...")
        sql = """SELECT * FROM accounts"""
        account_rows = self.db.query(sql)
        for row in account_rows:
            account = Account(row["id"], row["version"], row["name"], row["bank"])
            self.update_account(account)

            logger.debug("Fetching transactions for account %s", account)
            for trow in self.db.query("SELECT * FROM transactions WHERE account = ?", (account.id,)):
                category = category_repository.get_category_repository().get_category(trow["category"])
                transaction = Transaction(trow["id"], trow["version"], account, trow["serial"], trow["date"],
                                          trow["amount"], trow["name"], trow["description"], trow["counter_account"],
                                          trow["balance_after"], trow["reference"], category)
                self.update_transaction(transaction)
                account.add_transaction(transaction)

        logger.info("Cache initialized...")


class _AccountRepository(AccountRepository):
    """
    TODO: Consider incorporating an ORM, instead of building my own cache.
    """

    def __init__(self, db, cache):
        self.db = db
        self._cache = cache
        self._create_tables()

    def update_account(self, account):
        cursor = self.db.connection.cursor()
        if self.get_account_by_id(account.id):
            cursor.execute("UPDATE accounts SET version=?, name=?, bank=? WHERE id=?",
                           (account.version, account.name, account.bank, account.id))
        else:
            cursor.execute("INSERT INTO accounts (id, version, name, bank) VALUES (?,?,?,?)",
                           (account.id, account.version, account.name, account.bank))
        if self._cache:
            self._cache.update_account(account)
        publish_domain_events(account.flush_domain_events())

    def update_transaction(self, transaction):
        cursor = self.db.connection.cursor()
        if self.get_transaction_by_id(transaction.id):
            cursor.execute(
                "UPDATE transactions SET version=?, amount=?, date=?, name=?, description=?, balance_after=?, "
                "serial=?, counter_account=?, reference=?, account=?, category=? "
                "WHERE id=? ",
                (transaction.version, transaction._amount, transaction.date, transaction.name, transaction.description,
                 transaction._balance_after, transaction.serial, transaction.counter_account, transaction.reference,
                 transaction.account.id, transaction.category and transaction.category.id or None,
                 transaction.id))
        else:
            cursor.execute(
                "INSERT INTO transactions (id, version, amount, date, name, description, balance_after, serial,"
                "counter_account, reference, account, category)"
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (transaction.id, transaction.version, int(transaction._amount), transaction.date,
                 transaction.name,
                 transaction.description, int(transaction._balance_after), transaction.serial,
                 transaction.counter_account, transaction.reference, transaction.account.id,
                 transaction.category and transaction.category.id or None))
        if self._cache:
            self._cache.update_transaction(transaction)

        publish_domain_events(transaction.flush_domain_events())
        return transaction

    def get_accounts(self):
        if self._cache:
            return self._cache.get_accounts()
        else:
            sql = """SELECT * FROM accounts"""
            account_rows = self.db.query(sql)
            accounts = []
            for row in account_rows:
                account = Account(row["id"], row["version"], row["name"], row["bank"])
                accounts.append(self._collect_transactions(account))
            return accounts

    def get_account_by_id(self, id):
        if self._cache:
            return self._cache.get_account_by_id(id)
        else:
            row = self.db.query_one("SELECT * FROM accounts WHERE id=?", (id,))
            if row:
                account = Account(row["id"], row["version"], row["name"], row["bank"])
                if self._cache:
                    self._cache.update_account(account)
                return self._collect_transactions(account)
            else:
                return None

    def get_transaction_by_id(self, id):
        if self._cache:
            transaction = self._cache.get_transaction_by_id(id)
            return transaction
        else:
            row = self.db.query_one("SELECT * FROM transactions WHERE id=?", (id,))
            if row:
                transaction = Transaction(row["id"], row["version"], row["account"], row["serial"], row["date"],
                                          row["amount"], row["name"], row["description"], row["counter_account"],
                                          row["balance_after"], row["reference"], row["category"])
                if self._cache:
                    self._cache.update_transaction(transaction)
                return transaction
            else:
                return None

    def get_account_by_name(self, name):
        if self._cache:
            return self._cache.get_account_by_name(name)
        else:
            row = self.db.query_one("SELECT * FROM accounts WHERE name=?", (name,))
            if row:
                account = Account(row["id"], row["version"], row["name"], row["bank"])
                return self._collect_transactions(account)
            else:
                return None

    def _collect_transactions(self, account):
        logger.debug("Fetching transactions for account %s", account)
        for trow in self.db.query("SELECT * FROM transactions WHERE account = ?", (account.id,)):
            account.add_transaction(Transaction(trow["id"], trow["version"], account, trow["serial"], trow["date"],
                                                trow["amount"], trow["name"], trow["description"],
                                                trow["counter_account"], trow["balance_after"], trow["reference"],
                                                trow["category"]))
        return account

    def _create_tables(self):
        sql_create_accounts_table = """CREATE TABLE IF NOT EXISTS accounts (
                                        id text PRIMARY KEY,
                                        version integer NOT NULL,
                                        name text NOT NULL,
                                        bank text NOT NULL
                                        );"""
        sql_create_transactions_table = """CREATE TABLE IF NOT EXISTS transactions (
                                            id text PRIMARY KEY,
                                            version integer NOT NULL,
                                            amount integer NOT NULL,
                                            date date NOT NULL,
                                            name text NOT NULL,
                                            description text NOT NULL,
                                            balance_after integer NOT NULL,
                                            serial integer,
                                            counter_account text,
                                            reference text,
                                            account integer NOT NULL,
                                            category text,
                                            FOREIGN KEY (account) REFERENCES accounts (id),
                                            FOREIGN KEY (category) REFERENCES categories (id)
                                            );"""
        cursor = self.db.connection.cursor()
        cursor.execute(sql_create_accounts_table)
        cursor.execute(sql_create_transactions_table)
        self.db.connection.commit()


class _AccountFactory(AccountFactory):
    def create_account(self, name, bank):
        logger.debug("Creating account: %s (%s)", name, bank)
        account = Account(uuid.uuid4().hex, 0, name, bank)
        account.register_domain_event(AccountCreatedEvent(account))
        return account

    def create_transaction(self, account, date, amount, name, description, serial, counter_account, balance_after,
                           reference):
        transaction = Transaction(uuid.uuid4().hex, 0, account, serial, date, int(amount * decimal.Decimal(100)), name,
                                  description,
                                  counter_account, int(balance_after * decimal.Decimal(100)), reference, category=None)
        transaction.register_domain_event(TransactionCreatedEvent(transaction))
        return transaction


_account_cache = None
_account_repository = _AccountRepository(get_database(), _account_cache)
_account_factory = _AccountFactory()


def enable_cache(enabled=True):
    global _account_cache
    if enabled:
        _account_cache = _AccountCache(get_database())
        _account_cache.init_cache()
    else:
        _account_cache = None
    _account_repository._cache = _account_cache


def get_account_repository():
    return _account_repository


def get_account_factory():
    return _account_factory
