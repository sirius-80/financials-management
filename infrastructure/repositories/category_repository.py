import logging
import sqlite3
import uuid

from account_management.domain.model.category import CategoryRepository, CategoryFactory, Category
from infrastructure.repositories import get_database

logger = logging.getLogger(__name__)


class _CategoryCache:
    def __init__(self, db):
        self.db = db
        self.categories = {}

    def update_category(self, category):
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
            if row:
                if row["parent"]:
                    parent = self.get_category(row["parent"]) or read_category_by_id(row["parent"])
                else:
                    parent = None
                category = self.get_category(row["id"]) or Category(row["id"], row["version"], row["name"], parent)
                self.update_category(category)
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
                category = self.get_category(row["id"]) or Category(row["id"], row["version"], row["name"], parent)
                self.update_category(category)
        except sqlite3.Error as e:
            logger.warning("%s: No data from database: %s", self, e)
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
            category = None
            for name in names:
                row = self.db.query_one("SELECT * FROM categories WHERE name = ? ", (name,))
                category = Category(row["id"], row["version"], row["name"], next_parent)
                next_parent = category
            return category

    def get_category(self, id):
        if self._cache:
            logger.debug("Retrieving category with id %s from cache", id)
            return self._cache.get_category(id)
        else:
            logger.debug("Retrieving category with id %s from database", id)
            row = self.db.query_one("SELECT * FROM categories WHERE id = ?", (id,))
            logger.debug("Got data: %s", row)
            if row["parent"]:
                parent = self.get_category(row["parent"])
            else:
                parent = None
            category = Category(row["id"], row["version"], row["name"], parent)
            if self._cache:
                self._cache.update_category(category)

            return category

    def get_categories(self):
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

    def update_category(self, category):
        logger.debug("%s: update_category(%s (id=%s))", self, category, category.id)
        cursor = self.db.connection.cursor()
        if not self.get_category_by_qualified_name(category.qualified_name):
            #     logger.debug("%s: Updating existing database entry %s (id=%s)", self, category, category.id)
            #     cursor.execute("UPDATE categories SET version=?, name=?, parent=? WHERE id=?",
            #                    (category.version, category.name, category.parent and category.parent.id or None,
            #                     category.id))
            # else:
            logger.debug("%s: Creating new database entry %s (id=%s)", self, category, category.id)
            cursor.execute("INSERT INTO categories (id, version, name, parent) VALUES (?, ?, ?, ?)",
                           (category.id, category.version, category.name,
                            category.parent and category.parent.id or None))
        if category.parent and not self.get_category_by_qualified_name(category.parent.qualified_name):
            self.update_category(category.parent)

        self._cache.update_category(category)

    def _create_tables(self):
        sql_create_categories_table = """CREATE TABLE IF NOT EXISTS categories (
                                            id text PRIMARY KEY,
                                            version integer NOT NULL,
                                            name text NOT NULL,
                                            parent text,
                                            FOREIGN KEY (parent) REFERENCES categories (id)
                                            );"""
        self.db.connection.cursor().execute(sql_create_categories_table)
        self.db.connection.commit()


class _CategoryFactory(CategoryFactory):
    def __init__(self, category_repository):
        self.repository = category_repository

    def create_category(self, name, parent=None):
        category = Category(uuid.uuid4().hex, 0, name,
                            parent and self.repository.get_category_by_qualified_name(parent.qualified_name)or None)
        # category = self._cache.get_category_by_qualified_name(_temp_category.qualified_name) or _temp_category
        return category

    def create_category_from_qualified_name(self, qualified_name):
        logger.debug("%s: Creating category from qualified name %s", self, qualified_name)
        category = None
        if not category:
            next_parent = None
            for name in qualified_name.split("::"):
                tmp_category = self.create_category(name, next_parent)
                category = self.repository.get_category_by_qualified_name(tmp_category.qualified_name) or tmp_category
                category.parent = next_parent
                logger.debug("%s: Created category %s (id=%s, parent=%s)", self, category, category.id, category.parent)
                next_parent = category
        return category


_category_cache = _CategoryCache(get_database())
_category_cache.init_cache()
_category_repository = _CategoryRepository(get_database(), _category_cache)
_category_factory = _CategoryFactory(_category_repository)


def get_category_repository():
    return _category_repository


def get_category_factory():
    return _category_factory
