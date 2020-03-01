import logging
from datetime import datetime
import sqlalchemy
from dependency_injector import providers

from domain.account_management.model.account import AccountRepository, Account, Transaction, account_repository
from domain.account_management.model.category import category_repository
from infrastructure.repositories import blackboard
from infrastructure.services import publish_domain_events

logger = logging.getLogger(__name__)


class AccountCache(AccountRepository):
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

        stored_account = self.get_account(transaction.account.id)
        stored_account.transactions = [transaction if transaction.id == t.id else t
                                       for t in stored_account.transactions]

    def get_accounts(self):
        return self.accounts.values()

    def get_account_by_name_and_bank(self, name, bank):
        cached = next(iter(a for a in self.accounts.values() if a.name == name and a.bank == bank), None)
        return cached

    def get_account(self, account_id):
        if account_id in self.accounts.keys():
            return self.accounts[account_id]
        else:
            return None

    def get_transaction(self, transaction_id):
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
                category = category_repository().get_category(trow["category"])
                date_str = trow["date"].split(" ")[0] # strip trailing characters (if any)
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                transaction = Transaction(trow["id"], account, trow["serial"], date,
                                          trow["amount"], trow["name"], trow["description"], trow["counter_account"],
                                          trow["balance_after"], trow["internal"], category)
                self.save_transaction(transaction)
                account.add_transaction(transaction)

        logger.info("Cache initialized...")


class DbAccountRepository(AccountRepository):
    """
    TODO: Consider incorporating an ORM, instead of using my own cache.
    """

    def __init__(self, db, cache):
        logger.info("Creating %s", self.__class__)
        self.db = db
        self._cache = cache
        self._create_tables()
        self._cache.init_cache()

    def save_account(self, account):
        if self.get_account(account.id):
            statement = self.db_accounts.update().where(self.db_accounts.id == account.id).values(name=account.c.name,
                                                                                                  bank=account.c.bank)
            self.db.connection.execute(statement)
        else:
            statement = self.db_accounts.insert().values(id=account.id, name=account.name, bank=account.bank)
            self.db.connection.execute(statement)
        if self._cache:
            self._cache.save_account(account)
        publish_domain_events(account.flush_domain_events())

    def save_transaction(self, transaction):
        if self.get_transaction(transaction.id):
            statement = self.db_transactions.update().where(self.db_transactions.c.id == transaction.id).values(
                amount=transaction.amount, date=transaction.date, name=transaction.name,
                description=transaction.description, balance_after=transaction.balance_after, serial=transaction.serial,
                counter_account=transaction.counter_account, account=transaction.account.id,
                internal=transaction.internal, category=transaction.category and transaction.category.id or None
            )
            self.db.connection.execute(statement)
        else:
            statement = self.db_transactions.insert().values(
                id=transaction.id, amount=transaction.amount, date=transaction.date, name=transaction.name,
                description=transaction.description, balance_after=transaction.balance_after, serial=transaction.serial,
                counter_account=transaction.counter_account, account=transaction.account.id,
                internal=transaction.internal, category=transaction.category and transaction.category.id or None
            )
            self.db.connection.execute(statement)
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

    def get_account(self, account_id):
        if self._cache:
            return self._cache.get_account(account_id)
        else:
            row = self.db.query_one("SELECT * FROM accounts WHERE id=?", (account_id,))
            if row:
                account = Account(row["id"], row["name"], row["bank"])
                if self._cache:
                    self._cache.save_account(account)
                return self._collect_transactions(account)
            else:
                return None

    def get_transaction(self, transaction_id):
        if self._cache:
            transaction = self._cache.get_transaction(transaction_id)
            return transaction
        else:
            row = self.db.query_one("SELECT * FROM transactions WHERE id=?", (transaction_id,))
            if row:
                transaction = Transaction(row["id"], row["account"], row["serial"], row["date"],
                                          row["amount"], row["name"], row["description"], row["counter_account"],
                                          row["balance_after"], row["internal"], row["category"])
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
                                                trow["counter_account"], trow["balance_after"], trow["internal"],
                                                trow["category"]))
        return account

    def _create_tables(self):
        meta = self.db.meta
        if self.db.get_engine().dialect.has_table(self.db.get_engine(), 'accounts'):
            self.db_accounts = sqlalchemy.Table('accounts', meta, autoload=True, autoload_with=self.db.get_engine())
            logger.info("%s", self.db_accounts.select())
        else:
            self.db_accounts = sqlalchemy.Table('accounts', meta,
                                                sqlalchemy.Column('id', sqlalchemy.Text, primary_key=True),
                                                sqlalchemy.Column('name', sqlalchemy.Text, nullable=False),
                                                sqlalchemy.Column('bank', sqlalchemy.Text, nullable=False))
        if self.db.get_engine().dialect.has_table(self.db.get_engine(), 'transactions'):
            self.db_transactions = sqlalchemy.Table('transactions', meta, autoload=True,
                                                    autoload_with=self.db.get_engine())
        else:
            self.db_transactions = sqlalchemy.Table('transactions', meta,
                                                    sqlalchemy.Column('id', sqlalchemy.Text, primary_key=True),
                                                    sqlalchemy.Column('amount', sqlalchemy.Numeric(15, 2),
                                                                      nullable=False),
                                                    sqlalchemy.Column('date', sqlalchemy.Date, nullable=False),
                                                    sqlalchemy.Column('name', sqlalchemy.Text, nullable=False),
                                                    sqlalchemy.Column('description', sqlalchemy.Text, nullable=False),
                                                    sqlalchemy.Column('balance_after', sqlalchemy.Numeric(15, 2),
                                                                      nullable=False),
                                                    sqlalchemy.Column('serial', sqlalchemy.Integer),
                                                    sqlalchemy.Column('counter_account', sqlalchemy.Text),
                                                    sqlalchemy.Column('account', sqlalchemy.Integer,
                                                                      sqlalchemy.ForeignKey('accounts.id'),
                                                                      nullable=False),
                                                    sqlalchemy.Column('internal', sqlalchemy.Boolean),
                                                    sqlalchemy.Column('category', sqlalchemy.Text,
                                                                      sqlalchemy.ForeignKey('categories.id'))
                                                    )
        meta.create_all(self.db.get_engine())


def init():
    blackboard.account_cache = providers.Singleton(AccountCache, db=blackboard.database)
    account_repository.provided_by(
        providers.Singleton(DbAccountRepository, db=blackboard.database, cache=blackboard.account_cache))
