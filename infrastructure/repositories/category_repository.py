import logging
import sqlite3

from domain.account_management.model.category import CategoryRepository, Category

logger = logging.getLogger(__name__)


class CategoryCache(CategoryRepository):
    def __init__(self, db):
        self.db = db
        self.categories = {}

    def save_category(self, category):
        if category.qualified_name not in self.categories.keys():
            logger.debug("Adding category %s (id=%s) to cache", category, category.id)
            self.categories[category.qualified_name] = category
        logger.debug("Updating category %s (categories: %s)", category, self.categories)
        assert category is self.categories[category.qualified_name]
        return category

    def get_categories(self):
        # logger.debug("Getting categories from cache: %s (size=%d)", self.categories, len(self.categories))
        return self.categories.values()

    def get_category_by_qualified_name(self, qualified_name):
        # logger.debug("Getting category with qualified name %s from cache (%s)", qualified_name, self.categories)
        cached = next(iter(c for c in self.categories.values() if c.qualified_name == qualified_name), None)
        # logger.debug("Got from cache: %s", cached)
        return cached

    def get_category(self, category_id):
        for cat in self.categories.values():
            if cat.id == category_id:
                return cat
        else:
            return None

    def init_cache(self):
        # logger.info("Initializing cache...")
        sql = """SELECT * FROM categories"""

        def read_category_by_id(category_id):
            row = self.db.query_one("SELECT * FROM categories WHERE id = ?", (category_id,))
            if row:
                if row["parent"]:
                    parent = self.get_category(row["parent"]) or read_category_by_id(row["parent"])
                else:
                    parent = None
                category = self.get_category(row["id"]) or Category(row["id"], row["name"], parent)
                self.save_category(category)
                if parent and category not in parent.children:
                    parent.children.append(category)
                    self.save_category(parent)
                return category
            else:
                return None

        try:
            category_rows = self.db.query(sql)
            for row in category_rows:
                parent_id = row["parent"]
                if parent_id:
                    parent = self.get_category(parent_id) or read_category_by_id(parent_id)
                    assert parent
                else:
                    parent = None
                category = self.get_category(row["id"]) or Category(row["id"], row["name"], parent)
                self.save_category(category)
                if parent and category not in parent.children:
                    parent.children.append(category)
                    self.save_category(parent)
        except sqlite3.Error as e:
            logger.warning("%s: No data from database: %s", self, e)
        # logger.info("Cache initialized...")


class DbCategoryRepository(CategoryRepository):
    def __init__(self, db, cache):
        self.db = db
        self._cache = cache
        self._create_tables()
        self._cache.init_cache()

    def get_category_by_qualified_name(self, qualified_name):
        return self._cache.get_category_by_qualified_name(qualified_name)

    def get_category(self, category_id):
        logger.debug("Retrieving category with id %s from cache", category_id)
        return self._cache.get_category(category_id)

    def get_categories(self):
        return self._cache.get_categories()

    def save_category(self, category):
        logger.debug("%s: update_category(%s (id=%s))", self, category, category.id)
        cursor = self.db.connection.cursor()
        if not self.get_category_by_qualified_name(category.qualified_name):
            logger.debug("%s: Creating new database entry %s (id=%s)", self, category, category.id)
            cursor.execute("INSERT INTO categories (id, name, parent) VALUES (?, ?, ?)",
                           (category.id, category.name, category.parent and category.parent.id or None))
        if category.parent and not self.get_category_by_qualified_name(category.parent.qualified_name):
            if category not in category.parent.children:
                category.parent.children.append(category)
            self.save_category(category.parent)

        self._cache.save_category(category)

    def _create_tables(self):
        sql_create_categories_table = """CREATE TABLE IF NOT EXISTS categories (
                                            id text PRIMARY KEY,
                                            name text NOT NULL,
                                            parent text,
                                            FOREIGN KEY (parent) REFERENCES categories (id)
                                            );"""
        self.db.connection.cursor().execute(sql_create_categories_table)
        self.db.connection.commit()
