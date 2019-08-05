from account_management.domain.model import Entity


class Category(Entity):
    def __init__(self, category_id, category_version, name, parent=None):
        super().__init__(category_id, category_version)
        self.name = name
        self.parent = parent

    @property
    def qualified_name(self):
        if self.parent:
            r = repr(self.parent) + "::"
        else:
            r = ""
        return r + self.name

    def __repr__(self):
        return self.qualified_name

    def inherits_from(self, other_category):
        """Returns True if given other_category is an ancestor of this category. Returns False otherwise."""
        if self.parent:
            if self.parent == other_category:
                return True
            else:
                return self.parent.inherits_from(other_category)
        else:
            return False


class CategoryRepository:
    """Abstract class. Override with specific infrastructure."""

    def get_category_by_qualified_name(self, qualified_name):
        raise NotImplementedError

    def get_categories(self):
        raise NotImplementedError


class CategoryFactory:
    def create_category(self, name, parent=None):
        raise NotImplementedError
