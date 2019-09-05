import logging

import pubsub.pub

import application.services.afas
import application.services.data_export.native
import application.services.data_import.native
import application.services.data_import.rabobank
import domain.account_management
import infrastructure
from application.services.transaction_mapping import CategoryCleanupTransactionMapper, map_transaction, \
    InternalTransactionsMapper, MyInternalTransactionDetector

RABOBANK = "Rabobank"
logger = logging.getLogger(__name__)


def export_native_data(account_file, transaction_file, category_file):
    account_repository = infrastructure.Infrastructure.account_repository()
    category_repository = infrastructure.Infrastructure.category_repository()

    application.services.data_export.native.export_categories(category_repository.get_categories(), category_file)
    application.services.data_export.native.export_accounts(account_repository.get_accounts(), account_file,
                                                            transaction_file)


def import_native_data(account_file, transaction_file, category_file):
    account_repository = infrastructure.Infrastructure.account_repository()
    account_factory = domain.account_management.AccountManagement.account_factory()
    category_repository = infrastructure.Infrastructure.category_repository()
    category_factory = domain.account_management.AccountManagement.category_factory()

    application.services.data_import.native.import_categories(category_file, category_repository, category_factory)
    application.services.data_import.native.import_accounts(account_file, account_repository, account_factory)
    application.services.data_import.native.import_transactions(transaction_file, account_repository, account_factory,
                                                                category_repository, category_factory)


def import_rabobank_transactions(filename_list):
    for csv in filename_list:
        application.services.data_import.rabobank.import_transactions_from_rabobank_csv(csv, RABOBANK)


def generate_category(category_repository, category_factory, qualified_name):
    if not category_repository.get_category_by_qualified_name(qualified_name):
        category_repository.save_category(category_factory.create_category_from_qualified_name(qualified_name))


def generate_categories(categories_file, category_factory, category_repository):
    with open(categories_file) as text:
        for qualified_name in text:
            qualified_name = qualified_name.strip()
            if qualified_name:
                generate_category(category_repository, category_factory, qualified_name)
    infrastructure.Infrastructure.database().connection.commit()


def on_transaction_categorized_event(event):
    logger.debug("Changed category %s => %s for transaction %s", event.__class__.__name__, event.old_category,
                 event.new_category, event.transaction)


def flag_internal_transaction(transaction, internal_transactions_detector, account_repository):
    if internal_transactions_detector.is_internal_transaction(transaction):
        logger.debug("Flagging transaction as internal: %s", transaction)
        transaction.set_internal(True)
        account_repository.save_transaction(transaction)


def on_transaction_created_event(event):
    logger.debug("Categorizing new transaction: %s", event.transaction)
    pattern_transaction_mapper = application.services.Services.pattern_mapper()
    afas_transaction_mapper = application.services.afas.afas_mapper() #dependencies.Container.afas_mapper()
    cleanup_transaction_mapper = application.services.Services.cleanup_mapper()
    internal_transactions_mapper = application.services.Services.internal_transactions_mapper()

    map_transaction(event.transaction, pattern_transaction_mapper,
                    infrastructure.Infrastructure.account_repository())
    map_transaction(event.transaction, afas_transaction_mapper,
                    infrastructure.Infrastructure.account_repository())
    map_transaction(event.transaction, cleanup_transaction_mapper,
                    infrastructure.Infrastructure.account_repository())
    map_transaction(event.transaction, internal_transactions_mapper,
                    infrastructure.Infrastructure.account_repository())

    internal_transactions_detector = MyInternalTransactionDetector()
    flag_internal_transaction(event.transaction, internal_transactions_detector,
                              infrastructure.Infrastructure.account_repository())


def log_current_account_info(account_repository):
    logger.debug("accounts: %s", account_repository.get_accounts())
    for account in account_repository.get_accounts():
        last_date = account.get_last_transaction_date()
        logger.warning("Account: %s (%s): %s => € %8s", account.name, account.id, last_date,
                       account.get_balance_at(last_date))


def initialize_application():
    pubsub.pub.subscribe(on_transaction_categorized_event, "TransactionCategorizedEvent")
    pubsub.pub.subscribe(on_transaction_created_event, "TransactionCreatedEvent")
    if not infrastructure.Infrastructure.category_repository().get_categories():
        generate_categories(application.services.Services.config().get_file("categories.txt"),
                            domain.account_management.AccountManagement.category_factory(),
                            infrastructure.Infrastructure.category_repository())
