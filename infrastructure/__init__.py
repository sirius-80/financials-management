from dependency_injector import containers, providers

from . import repositories
from .repositories import category_repository, account_repository


class Infrastructure(containers.DeclarativeContainer):
    database = providers.Singleton(repositories.DatabaseSqlite3)
    category_cache = providers.Singleton(category_repository._CategoryCache, db=database)
    category_repository = providers.Singleton(category_repository._CategoryRepository, db=database,
                                              cache=category_cache)
    account_cache = providers.Singleton(account_repository._AccountCache, db=database)
    account_repository = providers.Singleton(account_repository._AccountRepository, db=database, cache=account_cache)
