import copy
import logging
import uuid

from dependency_injector import providers

import dependencies
from domain.account_management.model import Entity, DomainEvent

logger = logging.getLogger(__name__)


class Account(Entity):
    def __init__(self, account_id, name, bank):
        super().__init__(account_id)
        self.name = name
        self.bank = bank
        self.transactions = []

    def __repr__(self):
        return "{c}(id={id}, name={name}, bank={bank!r}".format(
            c=self.__class__.__name__,
            id=self.id,
            name=self.name,
            bank=self.bank
        )

    def get_combined_amount_for_category_in_month(self, category, date):
        """Returns the combined amount of transactions in the year and month specified by given date."""
        matched_transactions = [t for t in self.transactions if
                                t.date.month == date.month
                                and t.date.year == date.year
                                and (t.category == category or (t.category and t.category.inherits_from(category)))]
        return sum([t.amount for t in matched_transactions])

    def get_balance_at(self, date):
        """Returns the account balance at given date."""
        transaction = self._get_last_transaction_at_or_before(date)
        return transaction.balance_after

    def get_transactions_between(self, start_date, end_date):
        """Returns the list of transactions of given category that falls after given start_date (inclusive) and before
        given end_date (exclusive)"""
        matched_transactions = [t for t in self.transactions if start_date <= t.date < end_date]
        return matched_transactions

    def get_transactions_for_category_between(self, start_date, end_date, category):
        """Returns the list of transactions of given category that falls after given start_date (inclusive) and before
        given end_date (exclusive), that match given category."""
        matched_transactions = [t for t in self.transactions if
                                start_date <= t.date < end_date and (
                                        t.category == category or (t.category and t.category.inherits_from(category)))]
        return matched_transactions

    def add_transaction(self, transaction):
        """Adds given transaction to this account. Note that the caller is responsible that transactions are only
        added once to an account."""
        self.transactions.append(transaction)

    def get_first_transaction_date(self):
        logger.debug("Getting first transaction date for account %s", self)
        if self.transactions:
            transaction = self.transactions[0]
            for t in self.transactions:
                if t.date < transaction.date:
                    transaction = t
            return transaction.date
        else:
            return None

    def get_last_transaction_date(self):
        logger.debug("Getting last transaction date for account %s", self)
        if self.transactions:
            transaction = self.transactions[0]
            for t in self.transactions:
                if t.date > transaction.date:
                    transaction = t
            return transaction.date
        else:
            return None

    def _get_last_transaction_at_or_before(self, date):
        """Returns the last transaction at given date, or the last transaction that occurred before this date, if
        no transaction occurred on this specific date."""
        logger.debug("Getting last transaction before %s for account %s", date, self)
        if self.transactions:
            transaction = self.transactions[0]
            for t in self.transactions:
                if transaction.date <= t.date <= date:
                    transaction = t
            return transaction
        else:
            return None

    def get_transactions(self):
        return copy.copy(self.transactions)


class TransactionCategorizedEvent(DomainEvent):
    def __init__(self, transaction, old_category, new_category):
        self.transaction = transaction
        self.old_category = old_category
        self.new_category = new_category

    def __repr__(self):
        return "TransactionCategorizedEvent %s: %s => %s" % (self.transaction, self.old_category, self.new_category)


class TransactionSetInternalEvent(DomainEvent):
    def __init__(self, transaction, old_internal_flag, new_internal_flag):
        self.transaction = transaction
        self.old_internal = old_internal_flag
        self.new_internal = new_internal_flag

    def __repr__(self):
        return "TransactionInternalEvent %s: %s => %s" % (self.transaction, self.old_internal, self.new_internal)


class AccountCreatedEvent(DomainEvent):
    def __init__(self, account):
        self.account = account

    def __repr__(self):
        return "AccountCreatedEvent %s" % (self.account,)


class TransactionCreatedEvent(DomainEvent):
    def __init__(self, transaction):
        self.transaction = transaction

    def __repr__(self):
        return "TransactionCreatedEvent %s" % (self.transaction,)


class Transaction(Entity):
    def __init__(self, transaction_id, account, serial, date, amount, name, description,
                 counter_account, balance_after, internal=False, category=None):
        super().__init__(transaction_id)
        self.account = account
        self.serial = serial
        self.date = date
        self.amount = amount
        self.name = name
        self.description = description
        self.counter_account = counter_account
        self.balance_after = balance_after
        self.internal = internal
        self.category = category

    def __repr__(self):
        return "{c}(id={id!r}, account={account!r}, date={date!r}, amount={amount!r}, " \
               "name={name!r}, counter_account={counter!r}, description={description!r}, category={category!r}, " \
               "internal={internal!r})".format(
            c=self.__class__.__name__,
            id=self.id,
            account=self.account,
            date=self.date,
            amount=self.amount,
            name=self.name,
            counter=self.counter_account,
            description=self.description,
            category=self.category,
            internal=self.internal)

    def update_category(self, category):
        self.register_domain_event(TransactionCategorizedEvent(self, self.category, category))
        self.category = category

    def set_internal(self, internal):
        self.register_domain_event(TransactionSetInternalEvent(self, self.internal, internal))
        self.internal = internal


class AccountRepository:
    """Abstract class. Override with specific infrastructure."""

    def get_accounts(self):
        raise NotImplementedError

    def get_account(self, account_id):
        raise NotImplementedError

    def get_account_by_name_and_bank(self, name, bank):
        raise NotImplementedError

    def save_account(self, account):
        raise NotImplementedError

    def get_transaction(self, transaction_id):
        raise NotImplementedError

    def save_transaction(self, transaction):
        raise NotImplementedError


class AccountFactory:
    """Factory to create new Account and Transaction entities. Note that the caller is responsible to save the created
    instances using the AccountRepository."""

    def create_account(self, name, bank):
        logger.debug("Creating account: %s (%s)", name, bank)
        account = Account(uuid.uuid4().hex, name, bank)
        account.register_domain_event(AccountCreatedEvent(account))
        return account

    def create_transaction(self, account, date, amount, name, description, serial, counter_account, balance_after):
        transaction = Transaction(uuid.uuid4().hex, account, serial, date, amount, name, description, counter_account,
                                  balance_after)
        transaction.register_domain_event(TransactionCreatedEvent(transaction))
        return transaction


dependencies.Factories.account_factory = providers.Factory(AccountFactory)
