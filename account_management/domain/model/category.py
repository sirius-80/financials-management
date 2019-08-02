from account_management.domain.model import Entity


class Category(Entity):
    def __init__(self, category_id, category_version, name, parent):
        super().__init__(category_id, category_version)
        self.name = name
        self.parent = parent

    @property
    def qualified_name(self):
        return repr(self)

    def __repr__(self):
        if self.parent:
            r = repr(self.parent) + "::"
        else:
            r = ""
        return r + self.name


class CategoryRepository:
    """Abstract class. Override with specific infrastructure."""

    def get_category_by_qualified_name(self, qualified_name):
        raise NotImplementedError

    def get_all_categories(self):
        raise NotImplementedError


class CategoryFactory:
    def create_category(self, name, parent=None):
        raise NotImplementedError
