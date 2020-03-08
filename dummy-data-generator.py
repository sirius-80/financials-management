#!/usr/bin/env python
import datetime
import logging
import os
import random

import application.services.data_export.native
from domain.account_management.model.account import AccountFactory
from domain.account_management.model.category import Category, CategoryFactory
from infrastructure.repositories.account_repository import AccountCache
from infrastructure.repositories.category_repository import CategoryCache

logging.basicConfig(format='%(asctime)-15s %(levelname)-7s [%(name)s] %(message)s')
logging.getLogger("").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def generate_categories():
    category_names = [
        ("Income", 0, "yearly"),
        ("Income::Salary", 2700, "monthly"),
        ("Expenses", 0, "yearly"),
        ("Expenses::House", 0, "yearly"),
        ("Expenses::House::Mortgage", -500, "monthly"),
        ("Expenses::House::Maintenance", -1500, "yearly"),
        ("Expenses::Household", 0, "yearly"),
        ("Expenses::Household::Groceries", -400, "monthly"),
        ("Expenses::Household::Personal care", -100, "monthly"),
        ("Expenses::Household::Pets", -50, "monthly"),
        ("Expenses::Transportation", 0, "yearly"),
        ("Expenses::Transportation::Purchase", -12000, "5years"),
        ("Expenses::Transportation::Fuel", -110, "monthly"),
        ("Expenses::Transportation::Maintenance", -800, "yearly"),
        ("Expenses::Transportation::Taxes", -40, "monthly"),
        ("Expenses::Transportation::Parking", -8, "monthly"),
        ("Expenses::Transportation::Public transportation", -80, "yearly"),
        ("Expenses::Transportation::Insurance", -80, "monthly"),
        ("Expenses::Medical", 0, "yearly"),
        ("Expenses::Medical::Health insurance", -210, "monthly"),
        ("Expenses::Medical::Medicines", -15, "monthly"),
        ("Expenses::Medical::Dentist", -70, "yearly"),
        ("Expenses::Leisure", 0, "yearly"),
        ("Expenses::Leisure::Dining out", -15, "monthly"),
        ("Expenses::Leisure::Vacation", -1400, "yearly"),
        ("Expenses::Leisure::Hobbies", -400, "yearly"),
        ("Expenses::Miscellaneous", 0, "yearly"),
        ("Expenses::Miscellaneous::Charity", -11, "monthly"),
        ("Expenses::Miscellaneous::Fines", -90, "yearly"),
        ("Expenses::Clothes", -115, "monthly"),
        ("Expenses::Insurance", 0, "yearly"),
        ("Expenses::Insurance::Life insurance", -25, "monthly"),
        ("Expenses::Insurance::Other Insurances", -175, "monthly"),
        ("Expenses::Education", 0, "yearly"),
        ("Expenses::Education::Books", -300, "yearly"),
        ("Expenses::Education::Tuition fee", -2083, "yearly"),
        ("Expenses::Telecom", 0, "yearly"),
        ("Expenses::Telecom::Internet", -60, "monthly"),
        ("Expenses::Telecom::Mobile phone", -25, "monthly"),
        ("Expenses::Uncategorized", 0, "yearly"),
        ("Expenses::Uncategorized::To be classified", 0, "monthly"),
        ("Transfers", 0, "monthly"),
    ]
    for (qname, amount, frequency) in category_names:
        category = category_factory.create_category_from_qualified_name(qname)
        category.amount = amount
        category.frequency = frequency
        logger.error("Created category %s, for €%d, %s", category, category.amount, category.frequency)
        category_repo.save_category(category)


"""
TODO: [X] Select categories to use  
TODO: [ ] Generate categories (using repos)
TODO: [ ] Determine yearly, monthly or weekly amount per category
TODO: [ ] Use gaussian distribution to generate monthly or yearly amount per category
TODO: [ ] Generate single transaction for specific category and amount
TODO: [ ] Generate single year of data
TODO: [ ] Generate 10 years of data
TODO: [ ] Determine once per x year events (e.g. house maintenance, purchasing new car, ...) 
"""

category_repo = CategoryCache(None)
category_factory = CategoryFactory(category_repo)
account_repo = AccountCache(None)
account_factory = AccountFactory()


def generate_year():
    pass


"transaction_id,amount,date,name,description,balance_after,serial,counter_account,account,category"
"38e140db7043480e9e880ab3b91e5751,-600,2012-01-01,M.A. SCHEPERS-EGBERINK E,,939.33,525,151418292,fb314661177f4c61b22db76bd20dd803,Overboekingen"


def main(output_directory):
    """Generates accounts.csv, categories.csv and transactions.csv containing more or less representative dummy data,
    to use for demonstration purposes."""
    generate_categories()

    savings_account = account_factory.create_account("Savings account", "DummyBank")
    payments_account = account_factory.create_account("Payments account", "DummyBank")
    account_repo.save_account(savings_account)
    account_repo.save_account(payments_account)

    serial = 0
    for year in range(2015, 2020):
        for month in range(1, 13):
            for category in [cat for cat in category_repo.get_categories() if
                             cat.frequency == "monthly" and cat.amount != 0]:
                serial += 1
                t = create_transaction(category, year, month, payments_account, serial)
                t.update_category(category)
                account_repo.save_transaction(t)

        for category in [cat for cat in category_repo.get_categories() if cat.frequency == "yearly" and cat.amount]:
            t = create_transaction(category, year, 12, payments_account, serial)
            logger.info("Adding yearly transaction for category %s: %s", category, t)
            t.update_category(category)
            account_repo.save_transaction(t)

        date = datetime.date(year, 12, 31)
        logger.info("balance at %s: %d", date, payments_account.get_balance_at(date))
        logger.info("    Total income in %d  : €%.2f", year, payments_account.get_combined_amount_for_category(category_repo.get_category_by_qualified_name("Income::Salary"), date, "yearly"))
        logger.info("    Total expenses in %d: €%.2f", year, payments_account.get_combined_amount_for_category(category_repo.get_category_by_qualified_name("Expenses"), date, "yearly"))

    category_file = os.path.join(output_directory, "categories.csv")
    account_file = os.path.join(output_directory, "accounts.csv")
    transaction_file = os.path.join(output_directory, "transactions.csv")
    application.services.data_export.native.export_categories(category_repo.get_categories(), category_file)
    application.services.data_export.native.export_accounts(account_repo.get_accounts(), account_file, transaction_file)


def create_transaction(category, year, month, account, serial):
    amount = category.amount + int(random.random() * category.amount * 0.5)
    date = datetime.date(year, month, 1)
    name = category.name
    description = "payment for " + category.name
    balance_after = account.get_balance_at(datetime.date(year, month, 2)) + amount
    counter = ""
    t = account_factory.create_transaction(account, date, amount, name, description, serial, counter, balance_after)
    account.add_transaction(t)
    # logger.info("Created transaction %s", t)
    return t


if __name__ == "__main__":
    main("dummy-data")
