import decimal
import logging
import uuid

from account_management.domain.model.account import AccountRepository, Account, Bank, Transaction, AccountFactory
from infrastructure.repositories import get_database

logger = logging.getLogger(__name__)


class _AccountCache:
    def __init__(self, db):
        self.db = db
        self.accounts = {}
        self.banks = {}

    def update_account(self, account):
        if account.id not in self.accounts.keys():
            self.accounts[account.id] = account
        stored = account
        stored.__dict__ = account.__dict__
        # logger.debug("Updated account: %s (cached = %s)", stored, self.accounts)
        return stored

    def update_bank(self, bank):
        if bank.id not in self.banks.keys():
            self.banks[bank.id] = bank
        stored = self.get_bank_by_id(bank.id)
        stored.__dict__ = bank.__dict__
        return stored

    def update_transaction(self, transaction):
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

    def get_bank_by_id(self, id):
        if id in self.banks.keys():
            return self.banks[id]
        else:
            return None

    def init_cache(self):
        logger.info("Initializing cache...")
        sql = """SELECT * FROM accounts"""
        account_rows = self.db.query(sql)
        for row in account_rows:
            bank_id = row["bank"]
            bank_row = self.db.query_one("SELECT * FROM banks WHERE id = ? ", (bank_id,))
            bank = self.get_bank_by_id(bank_id) or Bank(bank_row["id"], bank_row["version"], bank_row["name"])

            account = Account(row["id"], row["version"], row["name"], bank)

            logger.debug("Fetching transactions for account %s", account)
            for trow in self.db.query("SELECT * FROM transactions WHERE account = ?", (account.id,)):
                account.add_transaction(Transaction(trow["id"], trow["version"], account, trow["serial"], trow["date"],
                                                    trow["amount"], trow["name"], trow["description"],
                                                    trow["counter_account"], trow["balance_after"], trow["reference"],
                                                    trow["category"]))

            self.update_account(account)
        logger.info("Cache initialized...")


class _AccountRepository(AccountRepository):
    """
    TODO: Consider incorporating an ORM, instead of building my own cache.
    """

    def __init__(self, db, cache):
        self.db = db
        self._cache = cache
        self._create_tables()

    def update_transaction(self, transaction):
        cursor = self.db.connection.cursor()
        cursor.execute(
            "UPDATE transactions SET "
            "version=?, "
            "amount=?, "
            "date=?, "
            "name=?, "
            "description=?, "
            "balance_after=?, "
            "serial=?, "
            "counter_account=?, "
            "reference=?, "
            "account=?, "
            "category=? "
            "WHERE id=? ",
            (transaction.version,
             transaction._amount,
             transaction.date,
             transaction.name,
             transaction.description,
             transaction._balance_after,
             transaction.serial,
             transaction.counter_account,
             transaction.reference,
             transaction.account.id,
             transaction.category.id,
             transaction.id))
        self._cache.update_transaction(transaction)
        return transaction

    def update_account(self, account):
        cursor = self.db.connection.cursor()
        cursor.execute("UPDATE accounts SET version=?, name=?, bank=? WHERE id=?",
                       (account.version, account.name, account.bank.id, account.id))
        if self._cache:
            self._cache.update_account(account)
        return account

    def get_accounts(self):
        if self._cache:
            return self._cache.get_accounts()
        else:
            sql = """SELECT * FROM accounts"""
            account_rows = self.db.query(sql)
            accounts = []
            for row in account_rows:
                bank = self.get_bank_by_id(row["bank"])
                account = Account(row["id"], row["version"], row["name"], bank)
                accounts.append(self._update_transactions(account))
            return accounts

    def get_bank_by_id(self, id):
        row = self.db.query_one("SELECT * FROM banks WHERE id=?", (id,))
        return Bank(row["id"], row["version"], row["name"])

    def get_bank_by_name(self, name):
        row = self.db.query_one("SELECT * FROM banks WHERE name=?", (name,))
        if row:
            return Bank(row["id"], row["version"], row["name"])
        else:
            return None

    def get_account_by_id(self, id):
        if self._cache:
            return self._cache.get_account_by_id(id)
        else:
            row = self.db.query_one("SELECT * FROM accounts WHERE id=?", (id,))
            if row:
                account_id = row["id"]
                bank_id = row["bank"]
                bank = self.get_bank_by_id(bank_id)
                account = Account(account_id, row["version"], row["name"], bank)
                return self._update_transactions(account)
            else:
                return None

    def get_account_by_name(self, name):
        if self._cache:
            return self._cache.get_account_by_name(name)
        else:
            row = self.db.query_one("SELECT * FROM accounts WHERE name=?", (name,))
            if row:
                bank = self.get_bank_by_id(row["bank"])
                account = Account(row["id"], row["version"], row["name"], bank)
                return self._update_transactions(account)
            else:
                return None

    def _update_transactions(self, account):
        logger.debug("Fetching transactions for account %s", account)
        for trow in self.db.query("SELECT * FROM transactions WHERE account = ?", (account.id,)):
            account.add_transaction(Transaction(trow["id"], trow["version"], account, trow["serial"], trow["date"],
                                                trow["amount"], trow["name"], trow["description"],
                                                trow["counter_account"], trow["balance_after"], trow["reference"],
                                                trow["category"]))
        return account

    def _create_tables(self):
        """TODO: Migrate amount/balance to INTEGER"""
        sql_create_banks_table = """CREATE TABLE IF NOT EXISTS banks (
                                    id text PRIMARY KEY,
                                    version integer NOT NULL,
                                    name text NOT NULL
                                    );"""
        sql_create_accounts_table = """CREATE TABLE IF NOT EXISTS accounts (
                                        id text PRIMARY KEY,
                                        version integer NOT NULL,
                                        name text NOT NULL,
                                        bank integer NOT NULL,
                                        FOREIGN KEY (bank) REFERENCES banks (id)
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
        cursor.execute(sql_create_banks_table)
        cursor.execute(sql_create_accounts_table)
        cursor.execute(sql_create_transactions_table)


class _AccountFactory(AccountFactory):

    def __init__(self, db, cache):
        self.db = db
        self._cache = cache

    def create_account(self, name, bank):
        logger.debug("Creating account: %s (%s)", name, bank)
        account = Account(uuid.uuid4().hex, 0, name, bank)
        cursor = self.db.connection.cursor()
        cursor.execute("INSERT INTO accounts (id, version, name, bank) VALUES (?,?,?,?)",
                       (account.id, account.version, account.name, account.bank.id))
        if self._cache:
            self._cache.update_account(account)
        return account

    def create_bank(self, name):
        logger.debug("Creating bank: %s", name)
        bank = Bank(uuid.uuid4().hex, 0, name)
        cursor = self.db.connection.cursor()
        logger.debug("Creating bank: %s", bank)
        cursor.execute("INSERT INTO banks (id, version, name) VALUES (?,?,?)", (bank.id, bank.version, bank.name))
        if self._cache:
            self._cache.update_bank(bank)
        return bank

    def create_transaction(self, account, date, amount, name, description, serial, counter_account, balance_after,
                           reference):
        transaction = Transaction(uuid.uuid4().hex, 0, account, serial, date, amount * decimal.Decimal(100), name,
                                  description,
                                  counter_account, balance_after * decimal.Decimal(100), reference, category=None)
        cursor = self.db.connection.cursor()
        cursor.execute("INSERT INTO transactions (id, version, amount, date, name, description, balance_after, serial,"
                       "counter_account, reference, account)"
                       "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (transaction.id, transaction.version, int(transaction._amount), transaction.date,
                        transaction.name,
                        transaction.description, int(transaction._balance_after), transaction.serial,
                        transaction.counter_account, transaction.reference, transaction.account.id))
        if self._cache:
            self._cache.update_transaction(transaction)
        return transaction


_account_cache = None
_account_repository = _AccountRepository(get_database(), _account_cache)
_account_factory = _AccountFactory(get_database(), _account_cache)


def enable_cache(enabled=True):
    global _account_cache
    if enabled:
        _account_cache = _AccountCache(get_database())
        _account_cache.init_cache()
        _account_repository._cache = _account_cache
        _account_factory._cache = _account_cache
    else:
        _account_cache = None


def get_account_repository():
    return _account_repository


def get_account_factory():
    return _account_factory
