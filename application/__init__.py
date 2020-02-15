import logging

import pubsub.pub

import application.services.afas
import application.services.data_export.native
import application.services.data_import.native
import application.services.data_import.rabobank
import infrastructure.repositories
import infrastructure.repositories.account_repository
import infrastructure.repositories.category_repository
from application.services.transaction_mapping import CategoryCleanupTransactionMapper, map_transaction, \
    InternalTransactionsMapper, MyInternalTransactionDetector
from domain.account_management.model.account import account_repository
from domain.account_management.model.category import category_repository, category_factory

RABOBANK = "Rabobank"
logger = logging.getLogger(__name__)


def export_native_data(account_file, transaction_file, category_file):
    application.services.data_export.native.export_categories(category_repository().get_categories(), category_file)
    application.services.data_export.native.export_accounts(account_repository().get_accounts(), account_file,
                                                            transaction_file)


def import_native_data(account_file, transaction_file, category_file):
    application.services.data_import.native.import_categories(category_file)
    application.services.data_import.native.import_accounts(account_file)
    application.services.data_import.native.import_transactions(transaction_file)


def import_rabobank_transactions(filename_list):
    for csv in filename_list:
        application.services.data_import.rabobank.import_transactions_from_rabobank_csv(csv, RABOBANK)


def import_rabobank_transactions_from_csv(csv_string):
    application.services.data_import.rabobank.import_transactions_from_rabobank_text(csv_string, RABOBANK)


def generate_category(qualified_name):
    if not category_repository().get_category_by_qualified_name(qualified_name):
        category_repository().save_category(category_factory().create_category_from_qualified_name(qualified_name))


def generate_categories(categories_file):
    with open(categories_file) as text:
        for qualified_name in text:
            qualified_name = qualified_name.strip()
            if qualified_name:
                generate_category(qualified_name)


def on_transaction_categorized_event(event):
    logger.debug("Changed category %s => %s for transaction %s", event.__class__.__name__, event.old_category,
                 event.new_category, event.transaction)


def flag_internal_transaction(transaction, internal_transactions_detector):
    if internal_transactions_detector.is_internal_transaction(transaction):
        logger.debug("Flagging transaction as internal: %s", transaction)
        transaction.set_internal(True)
        account_repository().save_transaction(transaction)


def on_transaction_created_event(event):
    logger.debug("Categorizing new transaction: %s", event.transaction)
    pattern_transaction_mapper = application.services.Services.pattern_mapper()
    afas_transaction_mapper = application.services.Services.afas_mapper()
    cleanup_transaction_mapper = application.services.Services.cleanup_mapper()
    internal_transactions_mapper = application.services.Services.internal_transactions_mapper()

    map_transaction(event.transaction, pattern_transaction_mapper)
    map_transaction(event.transaction, afas_transaction_mapper)
    map_transaction(event.transaction, cleanup_transaction_mapper)
    map_transaction(event.transaction, internal_transactions_mapper)

    internal_transactions_detector = MyInternalTransactionDetector()
    flag_internal_transaction(event.transaction, internal_transactions_detector)


def initialize_application():
    infrastructure.repositories.init()
    infrastructure.repositories.account_repository.init()
    infrastructure.repositories.category_repository.init()
    pubsub.pub.subscribe(on_transaction_categorized_event, "TransactionCategorizedEvent")
    pubsub.pub.subscribe(on_transaction_created_event, "TransactionCreatedEvent")
    if not category_repository().get_categories():
        generate_categories(application.services.Services.config().get_file("categories.txt"))
