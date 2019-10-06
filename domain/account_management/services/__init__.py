def find_transactions_by_attributes(account, date, serial, amount, name, counter_account, description):
    """Returns all transactions in given account that exactly match given set of attributes."""
    return [t for t in account.get_transactions() if
            t.date == date
            and t.serial == serial
            and t.amount == amount
            and t.name == name
            and t.counter_account == counter_account
            and t.description == description]


class TransactionCategoryMapper:
    """Superclass for mappers that can map a given transaction to one or more specific categories. Every category
    match is scored (numerical), where a higher score means a better match."""
    class CategoryScore:
        """Represents the numerical score of a single category for a transaction. The higher the score, the better the
        match is."""
        def __init__(self, category, score):
            self.category = category
            self.score = score

    def get_category_scores(self, transaction):
        """Returns a (possibly empty) list of CategoryScore objects, representing the matching categories and their
        respective scores for given transaction."""
        raise NotImplementedError


class InternalTransactionDetector:
    def is_internal_transaction(self, transaction):
        """Returns True if, and only if, given transaction is an internal transaction (i.e. between own accounts)."""
        raise NotImplementedError
