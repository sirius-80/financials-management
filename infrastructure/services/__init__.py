import re

from account_management.domain.services import TransactionCategoryMapper


class _TransactionCategoryMapper(TransactionCategoryMapper):
    def __init__(self, mapping_filename):
        self.names = {}
        print("Reading mapping from", mapping_filename)
        with open(mapping_filename, encoding="ISO-8859-1") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                name = row["Name"]
                descr = row["Description"]
                cat_name = row["Category"]
                try:
                    category = category_repo.get_by_name(cat_name)
                except:
                    print("Failed to get category for", cat_name)
                    raise
                self.names[(name, descr)] = category

    def match_value(self, name, descr):
        """Returns a numerical value for a match, that can be used to compare the quality of the matches."""
        value = 0
        if name:
            value += 100 + len(name)
        if descr:
            value += 100 + len(descr)
        return value

    def get_category_scores(self, transaction):
        matches = []
        # match_patterns = set()
        # TODO: Continue here
        for name, descr in self.names.keys():
            name_pattern = ".*%s.*" % name.lower()
            description_pattern = ".*%s.*" % descr.lower()
            if re.match(name_pattern, transaction.name.lower()) and re.match(description_pattern,
                                                                             transaction.description.lower()):
                # transaction.category = self.names[(name, descr)]
                category = self.names[(name, descr)]
                score = self.match_value(name, descr)
                category_score = TransactionCategoryMapper.CategoryScore(category, score, name_pattern, description_pattern)
                # matches.add(self.names[(name, descr)])
                matches.add(category_score)
                # match_patterns.add((name, descr))
                # return True
                # else:
                #     print("UNMATCH? '%s::%s' -> '%s::%s'" % (name, descr, transaction.name, transaction.description))
        # if len(matches) > 1:
        #     # Select the best match
        #     match_patterns = list(match_patterns)
        #     match_values = [self.match_value(m, d) for (m, d) in match_patterns]
        #     max_value = max(match_values)
        #     max_pattern = match_patterns[match_values.index(max_value)]
        #     transaction.category = self.names[max_pattern]
        #     # print("WARNING: Selecting %s => %s from multiple matches for transaction %s (%s)" % (str(max_pattern), str(transaction.category), str(transaction), str(matches)))
        # if matches:
        #     return True
        # else:
        #     return False

        return matches


_mapper = _TransactionCategoryMapper()


def get_mapper():
    return _mapper
