import logging

from domain.account_management.model.account import AccountRepository, Account, Transaction, AccountFactory
from infrastructure import publish_domain_events
from infrastructure.repositories import get_database, category_repository

logger = logging.getLogger(__name__)


class _AccountCache(AccountRepository):
    def __init__(self, db):
        self.db = db
        self.accounts = {}
        self.transactions = {}

    def save_account(self, account):
        if account.id not in self.accounts.keys():
            self.accounts[account.id] = account
        assert self.accounts[account.id] is account
        return account

    def save_transaction(self, transaction):
        if transaction.id not in self.transactions.keys():
            self.transactions[transaction.id] = transaction
        assert self.transactions[transaction.id] is transaction

        stored_account = self.get_account_by_id(transaction.account.id)
        stored_account.transactions = [transaction if transaction.id == t.id else t
                                       for t in stored_account.transactions]

    def get_accounts(self):
        # logger.debug("Getting accounts from cache: %s (size=%d)", self.accounts, len(self.accounts))
        return self.accounts.values()

    def get_account_by_name_and_bank(self, name, bank):
        # logger.debug("Getting account with name %s from cache (%s)", name, self.accounts)
        cached = next(iter(a for a in self.accounts.values() if a.name == name and a.bank == bank), None)
        # logger.debug("Got from cache: %s", cached)
        return cached

    def get_account_by_id(self, account_id):
        if account_id in self.accounts.keys():
            return self.accounts[account_id]
        else:
            return None

    def get_transaction_by_id(self, transaction_id):
        if transaction_id in self.transactions.keys():
            return self.transactions[transaction_id]
        else:
            return None

    def init_cache(self):
        logger.info("Initializing cache...")
        sql = """SELECT * FROM accounts"""
        account_rows = self.db.query(sql)
        for row in account_rows:
            account = Account(row["id"], row["name"], row["bank"])
            self.save_account(account)

            logger.debug("Fetching transactions for account %s", account)
            for trow in self.db.query("SELECT * FROM transactions WHERE account = ?", (account.id,)):
                category = category_repository.get_category_repository().get_category(trow["category"])
                transaction = Transaction(trow["id"], account, trow["serial"], trow["date"],
                                          trow["amount"], trow["name"], trow["description"], trow["counter_account"],
                                          trow["balance_after"], category)
                self.save_transaction(transaction)
                account.add_transaction(transaction)

        logger.info("Cache initialized...")


class _AccountRepository(AccountRepository):
    """
    TODO: Consider incorporating an ORM, instead of using my own cache.
    """

    def __init__(self, db, cache):
        self.db = db
        self._cache = cache
        self._create_tables()

    def save_account(self, account):
        cursor = self.db.connection.cursor()
        if self.get_account_by_id(account.id):
            cursor.execute("UPDATE accounts SET name=?, bank=? WHERE id=?",
                           (account.name, account.bank, account.id))
        else:
            cursor.execute("INSERT INTO accounts (id, name, bank) VALUES (?,?,?)",
                           (account.id, account.name, account.bank))
        if self._cache:
            self._cache.save_account(account)
        publish_domain_events(account.flush_domain_events())

    def save_transaction(self, transaction):
        cursor = self.db.connection.cursor()
        if self.get_transaction_by_id(transaction.id):
            cursor.execute(
                "UPDATE transactions SET amount=?, date=?, name=?, description=?, balance_after=?, "
                "serial=?, counter_account=?, account=?, category=? "
                "WHERE id=? ",
                (transaction.amount, transaction.date, transaction.name, transaction.description,
                 transaction.balance_after, transaction.serial, transaction.counter_account, transaction.account.id,
                 transaction.category and transaction.category.id or None, transaction.id))
        else:
            cursor.execute(
                "INSERT INTO transactions (id, amount, date, name, description, balance_after, serial,"
                "counter_account, account, category)"
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (transaction.id, transaction.amount, transaction.date, transaction.name,
                 transaction.description, transaction.balance_after, transaction.serial,
                 transaction.counter_account, transaction.account.id,
                 transaction.category and transaction.category.id or None))
        if self._cache:
            self._cache.save_transaction(transaction)

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
                account = Account(row["id"], row["name"], row["bank"])
                accounts.append(self._collect_transactions(account))
            return accounts

    def get_account_by_id(self, account_id):
        if self._cache:
            return self._cache.get_account_by_id(account_id)
        else:
            row = self.db.query_one("SELECT * FROM accounts WHERE id=?", (account_id,))
            if row:
                account = Account(row["id"], row["name"], row["bank"])
                if self._cache:
                    self._cache.save_account(account)
                return self._collect_transactions(account)
            else:
                return None

    def get_transaction_by_id(self, transaction_id):
        if self._cache:
            transaction = self._cache.get_transaction_by_id(transaction_id)
            return transaction
        else:
            row = self.db.query_one("SELECT * FROM transactions WHERE id=?", (transaction_id,))
            if row:
                transaction = Transaction(row["id"], row["account"], row["serial"], row["date"],
                                          row["amount"], row["name"], row["description"], row["counter_account"],
                                          row["balance_after"], row["category"])
                if self._cache:
                    self._cache.save_transaction(transaction)
                return transaction
            else:
                return None

    def get_account_by_name_and_bank(self, name, bank):
        if self._cache:
            return self._cache.get_account_by_name_and_bank(name, bank)
        else:
            row = self.db.query_one("SELECT * FROM accounts WHERE name=?", (name,))
            if row:
                account = Account(row["id"], row["name"], row["bank"])
                return self._collect_transactions(account)
            else:
                return None

    def _collect_transactions(self, account):
        logger.debug("Fetching transactions for account %s", account)
        for trow in self.db.query("SELECT * FROM transactions WHERE account = ?", (account.id,)):
            account.add_transaction(Transaction(trow["id"], account, trow["serial"], trow["date"],
                                                trow["amount"], trow["name"], trow["description"],
                                                trow["counter_account"], trow["balance_after"], trow["category"]))
        return account

    def _create_tables(self):
        sql_create_accounts_table = """CREATE TABLE IF NOT EXISTS accounts (
                                        id text PRIMARY KEY,
                                        name text NOT NULL,
                                        bank text NOT NULL
                                        );"""
        sql_create_transactions_table = """CREATE TABLE IF NOT EXISTS transactions (
                                            id text PRIMARY KEY,
                                            amount decimal NOT NULL,
                                            date date NOT NULL,
                                            name text NOT NULL,
                                            description text NOT NULL,
                                            balance_after decimal NOT NULL,
                                            serial integer,
                                            counter_account text,
                                            account integer NOT NULL,
                                            category text,
                                            FOREIGN KEY (account) REFERENCES accounts (id),
                                            FOREIGN KEY (category) REFERENCES categories (id)
                                            );"""
        cursor = self.db.connection.cursor()
        cursor.execute(sql_create_accounts_table)
        cursor.execute(sql_create_transactions_table)
        self.db.connection.commit()


_account_cache = None
_account_repository = _AccountRepository(get_database(), _account_cache)
_account_factory = AccountFactory()


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
