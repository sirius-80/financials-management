import datetime
import logging
import os

from dependency_injector import containers, providers

import application.services.transaction_mapping
import infrastructure
from . import afas

logger = logging.getLogger(__name__)


def get_combined_balance_at(date):
    accounts = infrastructure.Infrastructure.account_repository().get_accounts()
    balance = 0
    for account in accounts:
        balance += account.get_balance_at(date)
    return float(balance)


def get_combined_amount_for_category_in_month(category, date):
    accounts = infrastructure.Infrastructure.account_repository().get_accounts()
    amount = 0
    for account in accounts:
        amount += account.get_combined_amount_for_category_in_month(category, date)
    return float(amount)


def get_transactions_between(start_date, end_date):
    accounts = infrastructure.Infrastructure.account_repository().get_accounts()
    transactions = []
    for account in accounts:
        transactions.extend(account.get_transactions_between(start_date, end_date))
    return transactions


def get_transactions_for_category_between(start_date, end_date, category):
    accounts = infrastructure.Infrastructure.account_repository().get_accounts()
    transactions = []
    for account in accounts:
        transactions.extend(account.get_transactions_for_category_between(start_date, end_date, category))
    return transactions


def get_date_of_first_transaction():
    """Returns the date of the first transaction for all accounts."""
    accounts = infrastructure.Infrastructure.account_repository().get_accounts()
    first_date = datetime.date.today()
    for account in accounts:
        account_date = account.get_first_transaction_date()
        if account_date < first_date:
            first_date = account_date
    return first_date


def get_date_of_last_transaction():
    """Returns the date of the last transaction for all accounts."""
    accounts = infrastructure.Infrastructure.account_repository().get_accounts()
    last_date = datetime.date.today()
    for account in accounts:
        account_date = account.get_last_transaction_date()
        if account_date > last_date:
            last_date = account_date
    return last_date


def get_transaction_date_range(start_date=None, end_date=None, day_nr=1):
    """Returns a list of monthly dates starting at january 1st in the year of start_date, until the month in
    given last_date."""
    if not start_date:
        start_date = get_date_of_first_transaction()
    if not end_date:
        end_date = get_date_of_last_transaction()

    dates = []
    for year in range(start_date.year, end_date.year + 1):
        for month in range(1, 13):
            d = datetime.datetime(year, month, day_nr).date()
            dates.append(d)
            if d > end_date:
                logger.debug("Stopping at date %s", d)
                break

    return dates


class Configuration:
    def __init__(self):
        self.data_directory = os.environ.get("DATA_DIRECTORY", "data")

    def get_file(self, filename):
        return os.path.join(self.data_directory, filename)


class Services(containers.DeclarativeContainer):
    config = providers.Factory(Configuration)
    afas_mapper = providers.Singleton(afas.AfasTransactionCategoryMapper,
                                      category_repository=infrastructure.Infrastructure.category_repository,
                                      config=config)
    cleanup_mapper = providers.Singleton(transaction_mapping.CategoryCleanupTransactionMapper,
                                         category_repository=infrastructure.Infrastructure.category_repository)
    internal_transactions_mapper = providers.Singleton(transaction_mapping.InternalTransactionsMapper)
    pattern_mapper = providers.Singleton(transaction_mapping.PatternTransactionCategoryMapper,
                                         category_repository=infrastructure.Infrastructure.category_repository,
                                         config=config)
