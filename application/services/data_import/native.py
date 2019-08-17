import csv
import itertools
import logging

logger = logging.getLogger(__name__)


def import_categories(filename, repository, factory):
    with open(filename) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            category_id, qualified_name = row["category_id"], row["qualified_name"]
            category = repository.get_category_by_qualified_name(qualified_name)
            if not category:
                category = factory.create_category_from_qualified_name(qualified_name)
                category.id = category_id
                repository.save_category(category)
            else:
                logger.info("Skipping import of existing category %s", category)


def import_accounts(filename, repository, factory):
    if repository.get_accounts():
        logger.error("Native import of accounts is only allowed on an empty database!")
        return

    with open(filename) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            account_id, name, bank = row["account_id"], row["name"], row["bank"]
            account = repository.get_account(account_id)
            if not account:
                account = factory.create_account(name, bank)
                account.id = account_id
                repository.save_account(account)
            else:
                logger.info("Skipping import of existing account %s", account)


def import_transactions(filename, account_repository, account_factory, category_repository, category_factory):
    if list(itertools.chain.from_iterable([a.get_transactions() for a in account_repository.get_accounts()])):
        logger.error("Native import of transactions is only allowed on an empty transactions table!")
        return

    with open(filename) as csv_file:
        fieldnames = ["transaction_id""amount", "date", "name", "description", "balance_after", "serial",
                      "counter_account", "account", "category"]
        reader = csv.DictReader(csv_file)
        for row in reader:
            transaction_id = row["transaction_id"]
            amount = row["amount"]
            date = row["date"]
            name = row["name"]
            description = row["description"]
            balance_after = row["balance_after"]
            serial = row["serial"]
            counter_account = row["counter_account"]
            account_id = row["account"]
            category_qualified_name = row["category"]
            transaction = account_repository.get_transaction(transaction_id)
            account = account_repository.get_account(account_id)
            if not transaction:
                transaction = account_factory.create_transaction(account, date, amount, name, description, serial,
                                                                 counter_account, balance_after)
                transaction.id = transaction_id
                if category_qualified_name:
                    category = category_repository.get_category_by_qualified_name(category_qualified_name)
                    if not category:
                        category = category_factory.create_category_from_qualified_name(category_qualified_name)
                        category_repository.save_category(category)
                    transaction.update_category(category)
            account_repository.save_transaction(transaction)
