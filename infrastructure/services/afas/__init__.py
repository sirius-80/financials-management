import csv

import datetime

from account_management.domain.services import TransactionCategoryMapper


def parse_csv(filename, category_repo):
    """Parses all csv-files into the list."""
    export = AfasExport()
    print("Reading ", filename)
    with open(filename, encoding="ISO-8859-1") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')

        for row in reader:
            try:
                account_id = row["accountnumber"]
                counter_account_id = row["counter_account_number"]
                date = datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
                try:
                    date2 = datetime.datetime.strptime(row["date2"], "%Y-%m-%d").date()
                except ValueError:
                    date2 = date
                amount = float(row["amount"])
                if row["debit_credit"] == 'D':
                    amount = -amount
                name = " ".join(row["name"].split())
                description = " ".join(row["description"].split())
                cat = row["category"]
                subcat = row["subcategory"]

                category = None
                try:
                    category = category_repo.get_category_by_qualified_name("Uitgaven::" + cat + "::" + subcat)
                except:
                    try:
                        category = category_repo.get_category_by_qualified_name(cat + "::" + subcat)
                    except:
                        print("Failed to get category for %s::%s" % (cat, subcat))
                        raise

                if category:
                    transaction = AfasTransaction(account_id, amount, date, date2, name, description,
                                                  counter_account_id, category)
                    export.add_transaction(transaction)
            except:
                print("Failed to read row", row)
                raise
    return export


class AfasTransaction:
    def __init__(self, account, amount, date, date2, name, description, counter_account, category):
        self.account = account
        self.amount = amount
        self.date = date
        self.date2 = date2
        self.name = name
        self.description = description
        self.counter_account = counter_account
        self.category = category

    def __repr__(self):
        return "€%.2f::%s::%s::%s" % (self.amount, self.date, self.name, self.description)


class AfasExport:
    """Contains exported data from AFAS. Can be used as a source for transaction categories."""

    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def get_category_for_analytics_transaction(self, transaction):
        matches = [t for t in self.transactions if t.amount == transaction.amount
                   and t.account in transaction.account.name
                   and (t.date == transaction.date or t.date2 == transaction.date)
                   and transaction.name in t.name
                   and t.counter_account in transaction.counter_account]
        # and (not t.description.strip() or not transaction.description.strip() or ("".join(t.description.split()) in "".join(transaction.description.split())))]
        if matches:
            if len(matches) >= 1:
                match = matches[0]
                self.transactions.remove(match)
                return match.category
            else:
                raise ValueError("Found zero matches for transaction %s" % str(transaction))
        else:
            pass
            # print("Found no match for transaction:", transaction)


class _AfasTransactionCategoryMapper(TransactionCategoryMapper):
    DEFAULT_SCORE = 100

    def __init__(self, afas_export_filename, category_repository):
        self.afas_export = parse_csv(afas_export_filename, category_repository)

    def get_category_scores(self, transaction):
        try:
            category = self.afas_export.get_category_for_analytics_transaction(transaction)
            return [TransactionCategoryMapper.CategoryScore(category, _AfasTransactionCategoryMapper.DEFAULT_SCORE)]
        except ValueError:
            return None


def get_afas_mapper(mapping_file, category_repository):
    return _AfasTransactionCategoryMapper(mapping_file, category_repository)
