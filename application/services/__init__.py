import datetime
import logging
import os

import dateutil
import dateutil.relativedelta
from dependency_injector import containers, providers

import application.services.transaction_mapping
from domain.account_management.model.account import account_repository
from . import afas

logger = logging.getLogger(__name__)


def get_combined_balance_at(date):
    accounts = account_repository().get_accounts()
    balance = 0
    for account in accounts:
        balance += account.get_balance_at(date)
    return float(balance)


def get_combined_amount_for_category(category, date, mode='monthly'):
    if mode == 'monthly':
        date_delta = dateutil.relativedelta.relativedelta(months=1)
    else:
        date_delta = dateutil.relativedelta.relativedelta(years=1)

    accounts = account_repository().get_accounts()
    amount = 0
    for account in accounts:
        amount += account.get_combined_amount_for_category(category, date, mode)
    return float(amount)


def get_combined_amount_for_category_in_month(category, date):
    accounts = account_repository().get_accounts()
    amount = 0
    for account in accounts:
        amount += account.get_combined_amount_for_category_in_month(category, date)
    return float(amount)


def get_transactions(start_date, end_date):
    accounts = account_repository().get_accounts()
    transactions = []
    for account in accounts:
        transactions.extend(account.get_transactions(start_date, end_date))
    return transactions


def get_transactions_for_category(start_date, end_date, category):
    accounts = account_repository().get_accounts()
    transactions = []
    for account in accounts:
        transactions.extend(account.get_transactions_for_category(start_date, end_date, category))
    return transactions


def get_date_of_first_transaction():
    """Returns the date of the first transaction for all accounts."""
    accounts = account_repository().get_accounts()
    first_date = datetime.date.today()
    for account in accounts:
        account_date = account.get_first_transaction_date()
        if account_date < first_date:
            first_date = account_date
    return first_date


def get_date_of_last_transaction():
    """Returns the date of the last transaction for all accounts."""
    accounts = account_repository().get_accounts()
    last_date = datetime.date.today()
    for account in accounts:
        account_date = account.get_last_transaction_date()
        if account_date > last_date:
            last_date = account_date
    return last_date


def get_transaction_date_range(start_date=None, end_date=None, day_nr=1, mode='monthly'):
    """Returns a list of monthly dates starting at january 1st in the year of start_date, until the month in
    given last_date.
    TODO: Create equivalent function to get date-range for yearly dates (instead of monthly), to simplify UI/frontend
          code.
    """
    if not start_date:
        start_date = get_date_of_first_transaction()
    if not end_date:
        end_date = get_date_of_last_transaction()

    dates = []

    if mode == 'monthly':
        for year in range(start_date.year, end_date.year + 1):
            for month in range(1, 13):
                d = datetime.datetime(year, month, day_nr).date()
                dates.append(d)
                if d > end_date:
                    logger.debug("Stopping at date %s", d)
                    break
    else:
        for year in range(start_date.year, end_date.year + 1):
            d = datetime.datetime(year, 1, day_nr).date()
            dates.append(d)
            if d > end_date:
                logger.debug("Stopping at date %s", d)
                break

    return dates


def get_income_expenses_profit_loss(date_list, mode='monthly'):
    if mode == 'monthly':
        date_delta = dateutil.relativedelta.relativedelta(months=1)
    else:
        date_delta = dateutil.relativedelta.relativedelta(years=1)

    transactions = [get_transactions(date, date + date_delta) for date in date_list]

    income = []
    expenses = []
    for transaction_list in transactions:
        income_transactions = [t.amount for t in transaction_list if t.amount > 0 and not t.internal]
        expenses_transactions = [t.amount for t in transaction_list if t.amount < 0 and not t.internal]
        income.append(
            sum(income_transactions))
        expenses.append(
            sum(expenses_transactions))

    profit = []
    loss = []
    for money_in, money_out in zip(income, expenses):
        profit_loss = money_in + money_out
        if profit_loss > 0:
            profit.append(profit_loss)
            loss.append(0)
        else:
            loss.append(profit_loss)
            profit.append(0)

    return income, expenses, profit, loss


class Configuration:
    def __init__(self):
        self.data_directory = os.environ.get("DATA_DIRECTORY", "data")

    def get_file(self, filename):
        return os.path.join(self.data_directory, filename)


class Services(containers.DeclarativeContainer):
    config = providers.Factory(Configuration)
    afas_mapper = providers.Singleton(afas.AfasTransactionCategoryMapper, config=config)
    cleanup_mapper = providers.Singleton(transaction_mapping.CategoryCleanupTransactionMapper)
    internal_transactions_mapper = providers.Singleton(transaction_mapping.InternalTransactionsMapper)
    pattern_mapper = providers.Singleton(transaction_mapping.PatternTransactionCategoryMapper, config=config)
