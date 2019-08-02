from account_management.domain.model import Entity


class Category(Entity):
    def __init__(self, category_id, category_version, qualified_name, parent):
        super().__init__(category_id, category_version)
        self.qualified_name = qualified_name
        self.parent = parent

    @property
    def name(self):
        return repr(self)

    def __repr__(self):
        if self.parent:
            r = repr(self.parent) + "::"
        else:
            r = ""
        return r + self.name


class CategoryRepository:
    """Abstract class. Override with specific infrastructure."""

    def get_category(self, qualified_name):
        raise NotImplementedError

    def get_all_categories(self):
        raise NotImplementedError


class CategoryFactory:
    def create_category(self, name, parent=None):
        raise NotImplementedError
