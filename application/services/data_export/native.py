import csv


def _account_to_dict(account):
    return {"account_id": account.id, "name": account.name, "bank": account.bank}


def _transaction_to_dict(transaction):
    return {"transaction_id": transaction.id, "amount": transaction.amount, "date": transaction.date,
            "name": transaction.name, "description": transaction.description,
            "balance_after": transaction.balance_after, "serial": transaction.serial,
            "counter_account": transaction.counter_account, "account": transaction.account.id,
            "category": transaction.category and transaction.category.qualified_name or None}


def export_accounts(account_list, account_filename, transaction_filename):
    with open(account_filename, 'w') as account_csv_file, open(transaction_filename, 'w') as transaction_csv_file:
        account_fieldnames = ["account_id", "name", "bank"]
        account_writer = csv.DictWriter(account_csv_file, fieldnames=account_fieldnames)
        account_writer.writeheader()
        transaction_fieldnames = ["transaction_id", "amount", "date", "name", "description", "balance_after", "serial",
                                  "counter_account", "account", "category"]
        transaction_writer = csv.DictWriter(transaction_csv_file, fieldnames=transaction_fieldnames)
        transaction_writer.writeheader()
        for account in account_list:
            account_writer.writerow(_account_to_dict(account))
            for transaction in account.get_transactions():
                transaction_writer.writerow(_transaction_to_dict(transaction))


def export_categories(category_list, category_filename):
    with open(category_filename, 'w') as csv_file:
        category_fieldnames = ["category_id", "qualified_name"]
        category_writer = csv.DictWriter(csv_file, fieldnames=category_fieldnames)
        category_writer.writeheader()
        for category in category_list:
            category_writer.writerow({"category_id": category.id, "qualified_name": category.qualified_name})
