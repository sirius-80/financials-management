from dependency_injector import containers, providers

import domain.account_management.model.account
import domain.account_management.model.category
import infrastructure.repositories.account_repository
import infrastructure.repositories.category_repository


class Database(containers.DeclarativeContainer):
    database = providers.Singleton(infrastructure.repositories.DatabaseSqlite3)


class Caches(containers.DeclarativeContainer):
    account_cache = providers.Singleton(infrastructure.repositories.account_repository._AccountCache,
                                        db=Database.database)
    category_cache = providers.Singleton(infrastructure.repositories.category_repository._CategoryCache,
                                         db=Database.database)


class Repositories(containers.DeclarativeContainer):
    account_repository = providers.Singleton(infrastructure.repositories.account_repository._AccountRepository,
                                             db=Database.database, cache=Caches.account_cache)
    category_repository = providers.Singleton(infrastructure.repositories.category_repository._CategoryRepository,
                                              db=Database.database, cache=Caches.category_cache)


class Factories(containers.DeclarativeContainer):
    account_factory = providers.Factory(domain.account_management.model.account.AccountFactory)
    category_factory = providers.Factory(domain.account_management.model.category.CategoryFactory,
                                         category_repository=Repositories.category_repository)
