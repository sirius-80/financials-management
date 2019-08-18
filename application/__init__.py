import logging

# noinspection PyPackageRequirements
import pubsub.pub

import application.services.data_export.native
import application.services.data_import.native
import application.services.data_import.rabobank
import infrastructure
import infrastructure.services
import infrastructure.services.afas
from application.services.transaction_mapping import CategoryCleanupTransactionMapper, map_transaction, \
    InternalTransactionsMapper

RABOBANK = "Rabobank"
logger = logging.getLogger(__name__)


def export_native_data(account_file, transaction_file, category_file):
    account_repository = infrastructure.Repositories.account_repository()
    category_repository = infrastructure.Repositories.category_repository()

    application.services.data_export.native.export_categories(category_repository.get_categories(), category_file)
    application.services.data_export.native.export_accounts(account_repository.get_accounts(), account_file,
                                                            transaction_file)


def import_native_data(account_file, transaction_file, category_file):
    account_repository = infrastructure.Repositories.account_repository()
    account_factory = infrastructure.Factories.account_factory()
    category_repository = infrastructure.Repositories.category_repository()
    category_factory = infrastructure.Factories.category_factory()

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


def generate_categories(category_factory, category_repository):
    generate_category(category_repository, category_factory, "Inkomsten::Salaris Erik")
    generate_category(category_repository, category_factory, "Inkomsten::Salaris Marleen")
    generate_category(category_repository, category_factory, "Inkomsten::Belastingteruggaaf")
    generate_category(category_repository, category_factory, "Inkomsten::Belastingtoeslagen")
    generate_category(category_repository, category_factory, "Inkomsten::Schenking")
    generate_category(category_repository, category_factory, "Inkomsten::Kinderbijslag")
    generate_category(category_repository, category_factory, "Inkomsten::Rente")
    generate_category(category_repository, category_factory, "Inkomsten::Beleggingen/effecten")
    generate_category(category_repository, category_factory, "Inkomsten::Bijverdiensten")
    generate_category(category_repository, category_factory, "Inkomsten::Vakantiegeld")
    generate_category(category_repository, category_factory, "Inkomsten::Declaraties")
    generate_category(category_repository, category_factory, "Inkomsten::Bonussen")
    generate_category(category_repository, category_factory, "Inkomsten::Overige inkomsten")
    generate_category(category_repository, category_factory, "Inkomsten::Uitkering")

    generate_category(category_repository, category_factory, "Uitgaven::Wonen::Tuin")
    generate_category(category_repository, category_factory, "Uitgaven::Wonen::Hypotheek")
    generate_category(category_repository, category_factory, "Uitgaven::Wonen::Aflossing")
    generate_category(category_repository, category_factory, "Uitgaven::Wonen::Gas Water Licht")
    generate_category(category_repository, category_factory, "Uitgaven::Wonen::Inrichting")
    generate_category(category_repository, category_factory, "Uitgaven::Wonen::Gemeentelijke belastingen")
    generate_category(category_repository, category_factory, "Uitgaven::Wonen::Onderhoud")

    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Boodschappen")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Geldopnames")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Elektronica")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Huishoudelijke artikelen")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Huishoudster")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Persoonlijke verzorging")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Tijdschriften/kranten")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Huisdieren")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Kinderen")
    generate_category(category_repository, category_factory, "Uitgaven::Huishouden::Maatschappelijke organisaties")

    generate_category(category_repository, category_factory, "Uitgaven::Vervoer::Aanschaf")
    generate_category(category_repository, category_factory, "Uitgaven::Vervoer::Brandstof")
    generate_category(category_repository, category_factory, "Uitgaven::Vervoer::Onderhoud")
    generate_category(category_repository, category_factory, "Uitgaven::Vervoer::Wegenbelasting")
    generate_category(category_repository, category_factory, "Uitgaven::Vervoer::Parkeren")
    generate_category(category_repository, category_factory, "Uitgaven::Vervoer::Openbaar vervoer")
    generate_category(category_repository, category_factory, "Uitgaven::Vervoer::Brommer/fietsverzekering")

    generate_category(category_repository, category_factory, "Uitgaven::Medische kosten::Ziektekostenverzekering")
    generate_category(category_repository, category_factory, "Uitgaven::Medische kosten::Hulpmiddelen")
    generate_category(category_repository, category_factory, "Uitgaven::Medische kosten::Apotheek")
    generate_category(category_repository, category_factory, "Uitgaven::Medische kosten::Tandarts")
    generate_category(category_repository, category_factory, "Uitgaven::Medische kosten::Voeten")
    generate_category(category_repository, category_factory, "Uitgaven::Medische kosten::Fysiotherapeut")
    generate_category(category_repository, category_factory, "Uitgaven::Medische kosten::Alternatief")

    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Uit eten")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Cadeaus")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Uitstapjes")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Vakantie")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Hobby's")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Sport")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Abonnementen")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Verenigingen")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Loterijen")
    generate_category(category_repository, category_factory, "Uitgaven::Vrije tijd::Feest")

    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Sparen")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Overige uitgaven")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Kapper")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Goede doelen")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Zakgeld")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Bankkosten")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Overboekingen")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Kinderopvang")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Creditcard")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Schuldaflossing")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Boetes")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Debetrente")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Dienstreis")
    generate_category(category_repository, category_factory, "Uitgaven::Overige uitgaven::Abonnementen")

    generate_category(category_repository, category_factory, "Uitgaven::Kleding::Kleding")
    generate_category(category_repository, category_factory, "Uitgaven::Kleding::Schoenen")
    generate_category(category_repository, category_factory, "Uitgaven::Kleding::Sportkleding")

    generate_category(category_repository, category_factory, "Uitgaven::Verzekeringen::Levensverzekering")
    generate_category(category_repository, category_factory, "Uitgaven::Verzekeringen::Overige verzekeringen")

    generate_category(category_repository, category_factory, "Uitgaven::Educatie::Leermiddelen")
    generate_category(category_repository, category_factory, "Uitgaven::Educatie::Hulpmiddelen")
    generate_category(category_repository, category_factory, "Uitgaven::Educatie::Boeken")
    generate_category(category_repository, category_factory, "Uitgaven::Educatie::College/lesgeld")
    generate_category(category_repository, category_factory, "Uitgaven::Educatie::Cursussen")

    generate_category(category_repository, category_factory, "Uitgaven::Telecom::Internet/TV")
    generate_category(category_repository, category_factory, "Uitgaven::Telecom::Internet")
    generate_category(category_repository, category_factory, "Uitgaven::Telecom::Televisie")
    generate_category(category_repository, category_factory, "Uitgaven::Telecom::Mobiele telefoon")

    generate_category(category_repository, category_factory, "Uitgaven::Niet gecategoriseerd::Nog in te delen")

    generate_category(category_repository, category_factory, "Overboekingen")
    infrastructure.Database.database().connection.commit()


def on_transaction_categorized_event(event):
    logger.debug("Changed category %s => %s for transaction %s", event.__class__.__name__, event.old_category,
                 event.new_category, event.transaction)


def on_transaction_created_event(event):
    logger.debug("Categorizing new transaction: %s", event.transaction)
    pattern_transaction_mapper = infrastructure.services.get_pattern_mapper("mapping.csv",
                                                                            infrastructure.Repositories.category_repository())
    afas_transaction_mapper = infrastructure.services.afas.get_afas_mapper("AFAS2.csv",
                                                                           infrastructure.Repositories.category_repository())
    cleanup_transaction_mapper = CategoryCleanupTransactionMapper(
        infrastructure.Repositories.category_repository())
    internal_transactions_mapper = InternalTransactionsMapper()
    map_transaction(event.transaction, pattern_transaction_mapper,
                    infrastructure.Repositories.account_repository())
    map_transaction(event.transaction, afas_transaction_mapper,
                    infrastructure.Repositories.account_repository())
    map_transaction(event.transaction, cleanup_transaction_mapper,
                    infrastructure.Repositories.account_repository())
    map_transaction(event.transaction, internal_transactions_mapper,
                    infrastructure.Repositories.account_repository())


def log_current_account_info(account_repository):
    logger.debug("accounts: %s", account_repository.get_accounts())
    for account in account_repository.get_accounts():
        last_date = account.get_last_transaction_date()
        logger.warning("Account: %s (%s): %s => € %8s", account.name, account.id, last_date,
                       account.get_balance_at(last_date))


def initialize_application():
    pubsub.pub.subscribe(on_transaction_categorized_event, "TransactionCategorizedEvent")
    pubsub.pub.subscribe(on_transaction_created_event, "TransactionCreatedEvent")
    generate_categories(infrastructure.Factories.category_factory(),
                        infrastructure.Repositories.category_repository())
