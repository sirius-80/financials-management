# class TransactionService:
#     def __init__(self, account_repository, account_factory):
#         self.account_repository = account_repository
#         self.account_factory = account_factory
#
#     def book_transaction(self, account_id, date, amount, description, serial=None, counter_account=None,
#                          balance_after=None,
#                          reference=None):
#         account = self.account_repository.get_account_by_id(account_id)
#         if not balance_after:
#             balance_after = account.get_balance_at(date) + amount
#         if not serial:
#             last = account.get_last_transaction_at_or_before(date)
#             if last:
#                 serial = last.serial + 1
#             else:
#                 serial = 1
#         transaction = self.account_factory.create_transaction(self, date, amount, description, serial,
#                                                               counter_account, balance_after, reference)
#         account.add_transaction(transaction)
#         return transaction
import csv


def find_transactions_by_attributes(account, date, serial, amount, name, counter_account, description):
    matches = []
    for t in account.get_transactions():
        if t.date == date \
                and t.serial == serial \
                and t.amount == amount \
                and t.name == name \
                and t.counter_account == counter_account \
                and t.description == description:
            matches.append(t)
    return matches


class TransactionCategoryMapper:
    class CategoryScore:
        def __init__(self, category, score, _name_pattern=None, _description_pattern=None):
            self.category = category
            self.score = score
            self._name_pattern = _name_pattern
            self._description_pattern = _description_pattern

    def match_value(self, name, description):
        """Returns a numerical value for a match, that can be used to compare the quality of the matches."""
        raise NotImplementedError

    def get_category_scores(self, transaction):
        raise NotImplementedError

