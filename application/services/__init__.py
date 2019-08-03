import datetime

import infrastructure.repositories.account_repository


def get_combined_balance_at(date):
    accounts = infrastructure.repositories.account_repository.get_account_repository().get_accounts()
    balance = 0
    for account in accounts:
        balance += account.get_balance_at(date)
    return float(balance)


def get_combined_amount_for_category_in_month(category, date):
    accounts = infrastructure.repositories.account_repository.get_account_repository().get_accounts()
    amount = 0
    for account in accounts:
        amount += account.get_combined_amount_for_category_in_month(category, date)
    return float(amount)


def get_transactions_between(start_date, end_date, category):
    accounts = infrastructure.repositories.account_repository.get_account_repository().get_accounts()
    transactions = []
    for account in accounts:
        transactions.extend(account.get_transactions_between(start_date, end_date, category))
    return transactions


def get_date_of_first_transaction():
    """Returns the date of the first transaction for all accounts."""
    accounts = infrastructure.repositories.account_repository.get_account_repository().get_accounts()
    first_date = datetime.date.today()
    for account in accounts:
        account_date = account.get_first_transaction_date()
        if account_date < first_date:
            first_date = account_date
    return first_date


def get_date_of_last_transaction():
    """Returns the date of the last transaction for all accounts."""
    accounts = infrastructure.repositories.account_repository.get_account_repository().get_accounts()
    last_date = datetime.date.today()
    for account in accounts:
        account_date = account.get_last_transaction_date()
        if account_date > last_date:
            last_date = account_date
    return last_date


def get_transaction_date_range(start_date=None, end_date=None, day_nr=20):
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
                print("Stopping at date %s" % d)
                break

    return dates
