from dependency_injector import containers, providers

from .model import account, category


class AccountManagement(containers.DeclarativeContainer):
    category_factory = providers.Singleton(category.CategoryFactory)
    account_factory = providers.Singleton(account.AccountFactory)
