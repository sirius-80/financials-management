import os

from dependency_injector import containers, providers

import domain.account_management
import infrastructure.repositories
import infrastructure.repositories.account_repository
import infrastructure.repositories.category_repository
from application.services import afas, transaction_mapping


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


class Configuration:
    def __init__(self):
        self.data_directory = os.environ.get("DATA_DIRECTORY", "data")

    def get_file(self, filename):
        return os.path.join(self.data_directory, filename)


class Configurations(containers.DeclarativeContainer):
    config = providers.Factory(Configuration)


class Container(containers.DeclarativeContainer):
    afas_mapper = providers.Singleton(afas._AfasTransactionCategoryMapper,
                                      category_repository=Repositories.category_repository,
                                      config=Configurations.config)
    cleanup_mapper = providers.Singleton(transaction_mapping.CategoryCleanupTransactionMapper,
                                         category_repository=Repositories.category_repository)
    internal_transactions_mapper = providers.Singleton(
        transaction_mapping.InternalTransactionsMapper)
    pattern_mapper = providers.Singleton(transaction_mapping._PatternTransactionCategoryMapper,
                                         category_repository=Repositories.category_repository,
                                         config=Configurations.config)