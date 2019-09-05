from dependency_injector import containers, providers

from domain import Configuration


class Database(containers.DeclarativeContainer):
    database = None


class Caches(containers.DeclarativeContainer):
    account_cache = None
    category_cache = None


class Repositories(containers.DeclarativeContainer):
    account_repository = None
    category_repository = None


class Factories(containers.DeclarativeContainer):
    account_factory = None
    category_factory = None


class Configurations(containers.DeclarativeContainer):
    config = providers.Factory(Configuration)


class Container(containers.DeclarativeContainer):
    afas_mapper = None
    cleanup_mapper = None
    internal_transactions_mapper = None
    pattern_mapper = None
