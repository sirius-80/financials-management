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
        def __init__(self, category, score):
            self.category = category
            self.score = score

    def get_category_scores(self, transaction):
        raise NotImplementedError

