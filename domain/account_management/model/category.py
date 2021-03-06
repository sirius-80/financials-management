import logging
import uuid

from dependency_injector import providers

from domain.account_management.model import Entity

logger = logging.getLogger(__name__)


class Category(Entity):
    """A transaction Category marks"""

    def __init__(self, category_id, name, parent=None):
        super().__init__(category_id)
        self.name = name
        self.parent = parent
        self.children = []

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

    def get_categories(self):
        raise NotImplementedError

    def get_category(self, category_id):
        raise NotImplementedError

    def get_category_by_qualified_name(self, qualified_name):
        raise NotImplementedError

    def save_category(self, category):
        raise NotImplementedError


class CategoryFactory:
    """Factory to create new Category entities. Note that the caller is responsible to save the created
        instances using the CategoryRepository."""

    def __init__(self, category_repository):
        self.repository = category_repository

    def create_category(self, name, parent=None):
        category = Category(uuid.uuid4().hex, name,
                            parent and self.repository.get_category_by_qualified_name(parent.qualified_name) or None)
        return category

    def create_category_from_qualified_name(self, qualified_name):
        category = None
        if not category:
            next_parent = None
            for name in qualified_name.split("::"):
                tmp_category = self.create_category(name, next_parent)
                category = self.repository.get_category_by_qualified_name(tmp_category.qualified_name) or tmp_category
                category.parent = next_parent
                next_parent = category
        return category


logger.info("creating CategoryRepository dependency")
category_repository = providers.Dependency(instance_of=CategoryRepository)
category_factory = providers.Singleton(CategoryFactory, category_repository)
