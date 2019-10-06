import csv
import datetime
import logging

from domain.account_management.services import TransactionCategoryMapper
from domain.account_management.model.category import category_repository

logger = logging.getLogger(__name__)


def parse_csv(filename):
    """Parses all csv-files into the list."""
    export = AfasExport()
    logger.info("Reading AFAS export from %s", filename)
    try:
        with open(filename, encoding="ISO-8859-1") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=';')

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
                    sub_category = row["subcategory"]

                    try:
                        category = category_repository().get_category_by_qualified_name(
                            "Uitgaven::" + cat + "::" + sub_category)
                    except:
                        try:
                            category = category_repository().get_category_by_qualified_name(cat + "::" + sub_category)
                        except:
                            logger.warning("Failed to get category for %s::%s", cat, sub_category)
                            raise

                    if category:
                        transaction = AfasTransaction(account_id, amount, date, date2, name, description,
                                                      counter_account_id, category)
                        export.add_transaction(transaction)
                except:
                    logger.error("Failed to read row %s", row)
                    raise
    except FileNotFoundError:
        logger.warning(
            "No AFAS.csv found in data-directory. Will not use AFAS historical data to categorize transactions.")
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
        if matches:
            if len(matches) >= 1:
                match = matches[0]
                self.transactions.remove(match)
                return match.category
            else:
                raise ValueError("Found zero matches for transaction %s" % str(transaction))
        else:
            pass


class AfasTransactionCategoryMapper(TransactionCategoryMapper):
    DEFAULT_SCORE = 100

    def __init__(self, config):
        filename = config.get_file("AFAS.csv")
        self.afas_export = parse_csv(filename)

    def get_category_scores(self, transaction):
        try:
            category = self.afas_export.get_category_for_analytics_transaction(transaction)
            return [TransactionCategoryMapper.CategoryScore(category, AfasTransactionCategoryMapper.DEFAULT_SCORE)]
        except ValueError:
            return None
