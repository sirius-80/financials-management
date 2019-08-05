import csv
import re

from account_management.domain.services import TransactionCategoryMapper


class _PatternTransactionCategoryMapper(TransactionCategoryMapper):
    def __init__(self, mapping_filename, category_repository):
        self.category_repository = category_repository
        self.names = {}
        print("Reading mapping from", mapping_filename)
        with open(mapping_filename, encoding="ISO-8859-1") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=',')
            for row in reader:
                name = row["Name"]
                description = row["Description"]
                cat_name = row["Category"]
                try:
                    category = self.category_repository.get_category_by_qualified_name(cat_name)
                except:
                    print("Failed to get category for", cat_name)
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


_pattern_mapper = None


def get_pattern_mapper(mapping_file, category_repository):
    global _pattern_mapper
    if not _pattern_mapper:
        _pattern_mapper = _PatternTransactionCategoryMapper(mapping_file, category_repository)
    return _pattern_mapper
