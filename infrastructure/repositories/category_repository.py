import uuid

from account_management.domain.model.category import CategoryRepository, CategoryFactory, Category
from infrastructure.repositories import get_database


class _CategoryCache:
    def __init__(self, db):
        self.db = db
        self.categories = {}

    def update_category(self, category):
        if category.qualified_name not in self.categories.keys():
            self.categories[category.qualified_name] = category
        stored = category
        stored.__dict__ = category.__dict__
        # logger.debug("Updated category: %s (cached = %s)", stored, self.categories)
        return stored

    def get_categories(self):
        # logger.debug("Getting categories from cache: %s (size=%d)", self.categories, len(self.categories))
        return self.categories.values()

    def get_category_by_qualified_name(self, qname):
        # logger.debug("Getting category with qualified name %s from cache (%s)", qname, self.categories)
        cached = next(iter(c for c in self.categories.values() if c.qualified_name == qname), None)
        # logger.debug("Got from cache: %s", cached)
        return cached

    def get_category(self, id):
        for cat in self.categories.values():
            if cat.id == id:
                return cat
        else:
            return None

    def init_cache(self):
        # logger.info("Initializing cache...")
        sql = """SELECT * FROM categories"""

        def read_category_by_id(id):
            row = self.db.query_one("SELECT * FROM categories WHERE id = ?", (id,))
            if row["parent"]:
                parent = read_category_by_id(row["parent"])
            else:
                parent = None
            return Category(row["id"], row["version"], row["name"], parent)

        category_rows = self.db.query(sql)
        for row in category_rows:
            parent_id = row["parent"]
            if parent_id:
                parent = read_category_by_id(parent_id)
            else:
                parent = None
            category = Category(row["id"], row["version"], row["name"], parent)
            self.update_category(category)
        # logger.info("Cache initialized...")


class _CategoryRepository(CategoryRepository):
    def __init__(self, db, cache):
        self.db = db
        self._cache = cache
        self._create_tables()

    def get_category_by_qualified_name(self, qualified_name):
        if self._cache:
            return self._cache.get_category_by_qualified_name(qualified_name)
        else:
            names = qualified_name.split("::")
            next_parent = None
            for name in names:
                row = self.db.query_one("SELECT * FROM categories WHERE name = ? ", (name,))
                category = Category(row["id"], row["version"], row["name"], next_parent)
                next_parent = category
            return category

    def get_category(self, id):
        if self._cache:
            return self._cache.get_category(id)
        else:
            row = self.db.query_one("SELECT * FROM categories WHERE id = ?", (id, ))
            if row["parent"]:
                parent = self.get_category(row["parent"])
            else:
                parent = None
            return Category(row["id"], row["version"], row["name"], parent)

    def get_all_categories(self):
        if self._cache:
            return self._cache.get_categories()
        else:
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
            return categories

    def _create_tables(self):
        sql_create_categories_table = """CREATE TABLE IF NOT EXISTS categories (
                                            id text PRIMARY KEY,
                                            version integer NOT NULL,
                                            name text NOT NULL,
                                            parent text,
                                            FOREIGN KEY (parent) REFERENCES categories (id)
                                            );"""
        self.db.connection.cursor().execute(sql_create_categories_table)


class _CategoryFactory(CategoryFactory):
    def __init__(self, db, cache):
        self._db = db
        self._cache = cache

    def create_category(self, name, parent=None):
        _temp_category = Category(uuid.uuid4().hex, 0, name, parent)
        category = self._cache.get_category_by_qualified_name(_temp_category.qualified_name)
        if not category:
            category = Category(uuid.uuid4().hex, 0, name, parent)
            cursor = self._db.connection.cursor()
            if parent:
                cursor.execute("INSERT INTO categories (id, version, name, parent) VALUES (?, ?, ?, ?)",
                               (category.id, category.version, category.name, category.parent.id))
            else:
                cursor.execute("INSERT INTO categories (id, version, name) VALUES (?, ?, ?)",
                               (category.id, category.version, category.name))
        return category

    def create_category_from_qualified_name(self, qualified_name):
        next_parent = None
        for name in qualified_name.split("::"):
            category = self.create_category(name, next_parent)
            next_parent = category
        return category


_category_cache = _CategoryCache(get_database())
_category_repository = _CategoryRepository(get_database(), _category_cache)
_category_factory = _CategoryFactory(get_database(), _category_cache)
_category_cache.init_cache()


def get_category_repository():
    return _category_repository


def get_category_factory():
    return _category_factory
