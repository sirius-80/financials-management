from account_management.domain.services import TransactionCategoryMapper
import infrastructure.repositories.account_repository
import infrastructure.repositories.category_repository


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

    def __init__(self, category_repository):
        self.mapping = [
            (category_repository.get_category_by_qualified_name("Uitgaven::Overige uitgaven::Overboekingen"),
             category_repository.get_category_by_qualified_name("Overboekingen")),
            (category_repository.get_category_by_qualified_name("Uitgaven::Telecom::Televisie"),
             category_repository.get_category_by_qualified_name("Uitgaven::Telecom::Internet/TV")),
            (category_repository.get_category_by_qualified_name("Uitgaven::Telecom::Internet"),
             category_repository.get_category_by_qualified_name("Uitgaven::Telecom::Internet/TV")),
            (category_repository.get_category_by_qualified_name("Uitgaven::Overige uitgaven::Abonnementen"),
             category_repository.get_category_by_qualified_name("Uitgaven::Vrije tijd::Abonnementen")),
            (category_repository.get_category_by_qualified_name("Inkomsten::Belastingtoeslagen"),
             category_repository.get_category_by_qualified_name("Inkomsten::Belastingteruggaaf")),
        ]

    def get_category_scores(self, transaction):
        category_scores = []
        if transaction.category:
            new_category = [mapping[1] for mapping in self.mapping if mapping[0] == transaction.category]
            if new_category:
                category_scores.append(TransactionCategoryMapper.CategoryScore(new_category[0], self.DEFAULT_SCORE))
        return category_scores


class InternalTransactionsMapper(TransactionCategoryMapper):
    """Maps transactions between own accounts to the 'Overboekingen' category."""
    DEFAULT_SCORE = 100
    account_repository = infrastructure.repositories.account_repository.get_account_repository()
    internal_transactions_category = infrastructure.repositories.category_repository.get_category_repository().get_category_by_qualified_name(
        "Overboekingen")

    def get_category_scores(self, transaction):
        category_scores = []
        for account in self.account_repository:
            if account.name == transaction.counter_account:
                TransactionCategoryMapper.CategoryScore(self.internal_transactions_category, self.DEFAULT_SCORE)
        return category_scores


def get_best_scoring_category(category_score_list):
    """Returns the best scoring category from given list of CategoryScore objects.
    Returns None if given list is empty."""
    if category_score_list:
        category = next(iter(category_score_list)).category
    else:
        category = None
    return category


def map_transactions(transaction_mapper, account_repository, update=False):
    """Map all transactions from all accounts using given transaction_mapper. If the update flag is set to True, then
    transactions which have already been mapped will be updated. If the update flag is False, only uncategorized
    transactions will be processed."""
    for account in account_repository.get_accounts():
        for transaction in account.get_transactions():
            map_transaction(transaction, transaction_mapper, account_repository, update)


def map_transaction(transaction, transaction_mapper, account_repository, update=False):
    """Map given transaction using given transaction_mapper. If the update flag is set to True, then transactions which
    have already been mapped will be updated. If the update flag is False, only uncategorized transactions will be
    processed."""
    category_scores = transaction_mapper.get_category_scores(transaction)
    category = get_best_scoring_category(category_scores)
    if category:
        if (update or not transaction.category) and transaction.category != category:
            transaction.update_category(get_best_scoring_category(category_scores))
            account_repository.update_transaction(transaction)
