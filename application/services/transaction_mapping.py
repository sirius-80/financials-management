import csv
import logging
import re

from domain.account_management.model.account import account_repository
from domain.account_management.model.category import category_repository
from domain.account_management.services import TransactionCategoryMapper, InternalTransactionDetector

logger = logging.getLogger(__name__)


class CategoryCleanupTransactionMapper(TransactionCategoryMapper):
    """A mapper that maps transactions from one specific category to another specific category.
    Typically used to remove references to obsolete categories.

    For all transactions, map
       * Uitgaven::Overige uitgaven::Overboekingen => Overboekingen
       * Uitgaven::Telecom::Televisie => Uitgaven::Telecom::Internet/TV
       * Uitgaven::Telecom::Internet => Uitgaven::Telecom::Internet/TV
       * Uitgaven::Overige uitgaven::Abonnementen => Uitgaven::Vrije tijd::Abonnementen
       * Inkomsten::Belastingtoeslagen => Inkomsten::Belastingteruggaaf
    """
    DEFAULT_SCORE = 100

    def __init__(self):
        self.mapping = [
            (category_repository().get_category_by_qualified_name("Uitgaven::Overige uitgaven::Overboekingen"),
             category_repository().get_category_by_qualified_name("Overboekingen")),
            (category_repository().get_category_by_qualified_name("Uitgaven::Telecom::Televisie"),
             category_repository().get_category_by_qualified_name("Uitgaven::Telecom::Internet/TV")),
            (category_repository().get_category_by_qualified_name("Uitgaven::Telecom::Internet"),
             category_repository().get_category_by_qualified_name("Uitgaven::Telecom::Internet/TV")),
            (category_repository().get_category_by_qualified_name("Uitgaven::Overige uitgaven::Abonnementen"),
             category_repository().get_category_by_qualified_name("Uitgaven::Vrije tijd::Abonnementen")),
            (category_repository().get_category_by_qualified_name("Inkomsten::Belastingtoeslagen"),
             category_repository().get_category_by_qualified_name("Inkomsten::Belastingteruggaaf")),
        ]

    def get_category_scores(self, transaction):
        category_scores = []
        if transaction.category:
            new_category = [mapping[1] for mapping in self.mapping if mapping[0] == transaction.category]
            if new_category:
                category_scores.append(TransactionCategoryMapper.CategoryScore(new_category[0], self.DEFAULT_SCORE))
        return category_scores


class MyInternalTransactionDetector(InternalTransactionDetector):
    def is_internal_transaction(self, transaction):
        def extract_accountnr_from_iban(iban):
            m = re.search("^[A-Z]{2}[0-9]{2}[A-Z]+0*([0-9]+)$", iban)
            if m:
                return m.group(1)
            else:
                return iban

        for account in account_repository().get_accounts():
            if account.name == transaction.counter_account or extract_accountnr_from_iban(
                    account.name) == transaction.counter_account:
                return True
        return False


class InternalTransactionsMapper(TransactionCategoryMapper):
    """Maps transactions between own accounts to the 'Overboekingen' category."""
    def __init__(self):
        self.DEFAULT_SCORE = 100
        self.internal_transactions_detector = MyInternalTransactionDetector()
        self.internal_transactions_category = category_repository().get_category_by_qualified_name("Overboekingen")

    def get_category_scores(self, transaction):
        if self.internal_transactions_detector.is_internal_transaction(transaction):
            return [TransactionCategoryMapper.CategoryScore(self.internal_transactions_category, self.DEFAULT_SCORE)]
        else:
            return []


def get_best_scoring_category(category_score_list):
    """Returns the best scoring category from given list of CategoryScore objects.
    Returns None if given list is empty."""
    if category_score_list:
        category = next(iter(category_score_list)).category
    else:
        category = None
    return category


def map_transaction(transaction, transaction_mapper, update=False):
    """Map given transaction using given transaction_mapper. If the update flag is set to True, then transactions which
    have already been mapped will be updated. If the update flag is False, only uncategorized transactions will be
    processed."""
    category_scores = transaction_mapper.get_category_scores(transaction)
    category = get_best_scoring_category(category_scores)
    if category:
        if (update or not transaction.category) and transaction.category != category:
            transaction.update_category(category)
            account_repository().save_transaction(transaction)


class PatternTransactionCategoryMapper(TransactionCategoryMapper):
    def __init__(self, config):
        self.names = {}
        mapping_filename = config.get_file("mapping.csv")
        logger.info("Reading mapping from %s", mapping_filename)
        with open(mapping_filename, encoding="ISO-8859-1") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=',')
            for row in reader:
                name = row["Name"]
                description = row["Description"]
                cat_name = row["Category"]
                try:
                    category = category_repository().get_category_by_qualified_name(cat_name)
                except:
                    logger.warning("Failed to get category for %s", cat_name)
                    raise
                self.names[(name, description)] = category

    @staticmethod
    def match_value(name, description):
        """Returns a numerical value for a match, that can be used to compare the quality of the matches."""
        value = 0
        if name:
            value += 100 + len(name)
        if description:
            value += 100 + len(description)
        return value

    def get_category_scores(self, transaction):
        matches = []
        for name, description in self.names.keys():
            name_pattern = ".*%s.*" % name.lower()
            description_pattern = ".*%s.*" % description.lower()
            if re.match(name_pattern, transaction.name.lower()) and re.match(description_pattern,
                                                                             transaction.description.lower()):
                category = self.names[(name, description)]
                score = self.match_value(name, description)
                category_score = TransactionCategoryMapper.CategoryScore(category, score)
                matches.append(category_score)

        return sorted(matches, key=lambda cs: cs.score, reverse=True)
