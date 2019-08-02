import uuid

from account_management.domain.model.category import CategoryRepository, CategoryFactory, Category
from infrastructure.repositories import get_database


class _CategoryRepository(CategoryRepository):
    """TODO: Implement"""

    def __init__(self, db):
        self.db = db
        self._create_tables()

    def get_category(self, qualified_name):
        names = qualified_name.split("::")
        next_parent = None
        for name in names:
            row = self.db.query_one("SELECT * FROM category WHERE name = ? ", (name,))
            category = Category(row["id"], row["version"], row["name"], next_parent)
            next_parent = category
        return category

    def get_all_categories(self):
        categories = []

        # First construct all categories with parent id's (since the parent may not be constructed yet)
        for row in self.db.query("SELECT * FROM categories"):
            categories.append(Category(row["id"], row["version"], row["name"], row["parent"]))

        # Then resolve the parents
        for category in categories:
            if category.parent:
                parents = [cat for cat in categories if cat.id == category.parent]
                if len(parents) != 1:
                    raise ValueError("Category (%s) should have exactly 1 parent, but has %d (%s)",
                                     category, len(parents), parents)
            else:
                category.parent = None

    def _create_tables(self):
        sql_create_categories_table = """CREATE TABLE IF NOT EXISTS categories (
                                            id text PRIMARY KEY,
                                            version integer NOT NULL,
                                            name text NOT NULL,
                                            parent text
                                            FOREIGN KEY (parent) REFERENCES categories (id)
                                            );"""
        self.db.connection.cursor().execute(sql_create_categories_table)


class _CategoryFactory(CategoryFactory):
    """
    TODO: This factory may create multiple objects representing the same category
          (not sure whether this becomes a problem).
    """

    def __init__(self, db):
        self.db = db

    def create_category(self, name, parent=None):
        category = Category(uuid.uuid4().hex, 0, name, parent)
        cursor = self.db.connection.cursor()
        if parent:
            cursor.execute("INSERT INTO categories (id, version, name, parent)",
                           (category.id, category.version, category.name, category.parent.name))
        else:
            cursor.execute("INSERT INTO categories (id, version, name)",
                           (category.id, category.version, category.name))
        return category

    def create_category_from_qualified_name(self, qualified_name):
        next_parent = None
        for name in qualified_name.split("::"):
            category = self.create_category(name, next_parent)
            next_parent = category
        return category


_category_repository = _CategoryRepository(get_database())
_category_factory = _CategoryFactory(get_database())


def get_category_repository():
    return _category_repository


def get_category_factory():
    return _category_factory
