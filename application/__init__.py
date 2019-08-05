import logging

import pubsub.pub

import application.services.data_import
import infrastructure.repositories.account_repository
import infrastructure.repositories.category_repository
import infrastructure.services
import infrastructure.services.afas
from application.services.transaction_mapping import CategoryCleanupTransactionMapper, map_transaction, \
    InternalTransactionsMapper

RABOBANK_TWENTE_OOST = "Rabobank Twente Oost"
logger = logging.getLogger(__name__)


def import_transactions(account_repository, account_factory, filename_list):
    bank = account_repository.get_bank_by_name(RABOBANK_TWENTE_OOST)
    if not bank:
        bank = account_factory.create_bank(RABOBANK_TWENTE_OOST)

    for csv in filename_list:
        application.services.data_import.import_transactions_from_rabobank_csv(csv, bank)


def generate_categories(category_factory):
    category_factory.create_category_from_qualified_name("Inkomsten::Salaris Erik")
    category_factory.create_category_from_qualified_name("Inkomsten::Salaris Marleen")
    category_factory.create_category_from_qualified_name("Inkomsten::Belastingteruggaaf")
    category_factory.create_category_from_qualified_name("Inkomsten::Belastingtoeslagen")
    category_factory.create_category_from_qualified_name("Inkomsten::Schenking")
    category_factory.create_category_from_qualified_name("Inkomsten::Kinderbijslag")
    category_factory.create_category_from_qualified_name("Inkomsten::Rente")
    category_factory.create_category_from_qualified_name("Inkomsten::Beleggingen/effecten")
    category_factory.create_category_from_qualified_name("Inkomsten::Bijverdiensten")
    category_factory.create_category_from_qualified_name("Inkomsten::Vakantiegeld")
    category_factory.create_category_from_qualified_name("Inkomsten::Declaraties")
    category_factory.create_category_from_qualified_name("Inkomsten::Bonussen")
    category_factory.create_category_from_qualified_name("Inkomsten::Overige inkomsten")
    category_factory.create_category_from_qualified_name("Inkomsten::Uitkering")

    category_factory.create_category_from_qualified_name("Uitgaven::Wonen::Tuin")
    category_factory.create_category_from_qualified_name("Uitgaven::Wonen::Hypotheek")
    category_factory.create_category_from_qualified_name("Uitgaven::Wonen::Aflossing")
    category_factory.create_category_from_qualified_name("Uitgaven::Wonen::Gas Water Licht")
    category_factory.create_category_from_qualified_name("Uitgaven::Wonen::Inrichting")
    category_factory.create_category_from_qualified_name("Uitgaven::Wonen::Gemeentelijke belastingen")
    category_factory.create_category_from_qualified_name("Uitgaven::Wonen::Onderhoud")

    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Boodschappen")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Geldopnames")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Elektronica")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Huishoudelijke artikelen")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Huishoudster")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Persoonlijke verzorging")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Tijdschriften/kranten")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Huisdieren")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Kinderen")
    category_factory.create_category_from_qualified_name("Uitgaven::Huishouden::Maatschappelijke organisaties")

    category_factory.create_category_from_qualified_name("Uitgaven::Vervoer::Aanschaf")
    category_factory.create_category_from_qualified_name("Uitgaven::Vervoer::Brandstof")
    category_factory.create_category_from_qualified_name("Uitgaven::Vervoer::Onderhoud")
    category_factory.create_category_from_qualified_name("Uitgaven::Vervoer::Wegenbelasting")
    category_factory.create_category_from_qualified_name("Uitgaven::Vervoer::Parkeren")
    category_factory.create_category_from_qualified_name("Uitgaven::Vervoer::Openbaar vervoer")
    category_factory.create_category_from_qualified_name("Uitgaven::Vervoer::Brommer/fietsverzekering")

    category_factory.create_category_from_qualified_name("Uitgaven::Medische kosten::Ziektekostenverzekering")
    category_factory.create_category_from_qualified_name("Uitgaven::Medische kosten::Hulpmiddelen")
    category_factory.create_category_from_qualified_name("Uitgaven::Medische kosten::Apotheek")
    category_factory.create_category_from_qualified_name("Uitgaven::Medische kosten::Tandarts")
    category_factory.create_category_from_qualified_name("Uitgaven::Medische kosten::Voeten")
    category_factory.create_category_from_qualified_name("Uitgaven::Medische kosten::Fysiotherapeut")
    category_factory.create_category_from_qualified_name("Uitgaven::Medische kosten::Alternatief")

    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Uit eten")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Cadeaus")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Uitstapjes")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Vakantie")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Hobby's")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Sport")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Abonnementen")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Verenigingen")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Loterijen")
    category_factory.create_category_from_qualified_name("Uitgaven::Vrije tijd::Feest")

    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Sparen")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Overige uitgaven")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Kapper")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Goede doelen")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Zakgeld")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Bankkosten")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Overboekingen")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Kinderopvang")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Creditcard")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Schuldaflossing")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Boetes")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Debetrente")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Dienstreis")
    category_factory.create_category_from_qualified_name("Uitgaven::Overige uitgaven::Abonnementen")

    category_factory.create_category_from_qualified_name("Uitgaven::Kleding::Kleding")
    category_factory.create_category_from_qualified_name("Uitgaven::Kleding::Schoenen")
    category_factory.create_category_from_qualified_name("Uitgaven::Kleding::Sportkleding")

    category_factory.create_category_from_qualified_name("Uitgaven::Verzekeringen::Levensverzekering")
    category_factory.create_category_from_qualified_name("Uitgaven::Verzekeringen::Overige verzekeringen")

    category_factory.create_category_from_qualified_name("Uitgaven::Educatie::Leermiddelen")
    category_factory.create_category_from_qualified_name("Uitgaven::Educatie::Hulpmiddelen")
    category_factory.create_category_from_qualified_name("Uitgaven::Educatie::Boeken")
    category_factory.create_category_from_qualified_name("Uitgaven::Educatie::College/lesgeld")
    category_factory.create_category_from_qualified_name("Uitgaven::Educatie::Cursussen")

    category_factory.create_category_from_qualified_name("Uitgaven::Telecom::Internet/TV")
    category_factory.create_category_from_qualified_name("Uitgaven::Telecom::Internet")
    category_factory.create_category_from_qualified_name("Uitgaven::Telecom::Televisie")
    category_factory.create_category_from_qualified_name("Uitgaven::Telecom::Mobiele telefoon")

    category_factory.create_category_from_qualified_name("Uitgaven::Niet gecategoriseerd::Nog in te delen")

    category_factory.create_category_from_qualified_name("Overboekingen")
    infrastructure.repositories.get_database().connection.commit()


def transaction_categorized_event_listener(event):
    logger.debug("%s received: Category %s => %s for transaction %s", event.__class__.__name__, event.old_category,
                 event.new_category, event.transaction)


def on_transaction_created_event(event):
    logger.info("Categorizing new transaction: %s", event.transaction)
    pattern_transaction_mapper = infrastructure.services.get_pattern_mapper("mapping.csv",
                                                                            infrastructure.repositories.category_repository.get_category_repository())
    afas_transaction_mapper = infrastructure.services.afas.get_afas_mapper("AFAS2.csv",
                                                                           infrastructure.repositories.category_repository.get_category_repository())
    cleanup_transaction_mapper = CategoryCleanupTransactionMapper(
        infrastructure.repositories.category_repository.get_category_repository())
    internal_transactions_mapper = InternalTransactionsMapper()
    map_transaction(event.transaction, pattern_transaction_mapper,
                    infrastructure.repositories.account_repository.get_account_repository())
    map_transaction(event.transaction, afas_transaction_mapper,
                    infrastructure.repositories.account_repository.get_account_repository())
    map_transaction(event.transaction, cleanup_transaction_mapper,
                    infrastructure.repositories.account_repository.get_account_repository())
    map_transaction(event.transaction, internal_transactions_mapper,
                    infrastructure.repositories.account_repository.get_account_repository())


def initialize_database_when_empty(filename_list, account_repository):
    if not account_repository.get_accounts():
        import_transactions(account_repository, infrastructure.repositories.account_repository.get_account_factory(),
                            filename_list)
        infrastructure.repositories.get_database().connection.commit()


def log_current_account_info(account_repository):
    logger.debug("accounts: %s", account_repository.get_accounts())
    for account in account_repository.get_accounts():
        last_date = account.get_last_transaction_date()
        logger.warning("Account: %s (%s): %s => € %8s", account.name, account.id, last_date,
                       account.get_last_transaction_at_or_before(last_date).balance_after)


def initialize_application():
    account_repository = infrastructure.repositories.account_repository.get_account_repository()
    FORMAT = '%(asctime)-15s %(levelname)-7s [%(name)s] %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.getLogger("").setLevel(logging.DEBUG)
    pubsub.pub.subscribe(transaction_categorized_event_listener, "TransactionCategorizedEvent")
    pubsub.pub.subscribe(on_transaction_created_event, "TransactionCreatedEvent")
    generate_categories(infrastructure.repositories.category_repository.get_category_factory())

    # TODO: Control caching from cmd-line parameter?
    infrastructure.repositories.account_repository.enable_cache()
    initialize_database_when_empty(["transacties-20120101-to-20190430.csv", "transacties-20190501-to-20190725.csv"],
                                   account_repository)
    log_current_account_info(account_repository)
