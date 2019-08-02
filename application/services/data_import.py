import csv
import datetime
import decimal
import logging

from account_management.domain import services
import infrastructure.repositories.account_repository


def import_transactions_from_rabobank_csv(filename, bank):
    """Parses given csv-file export from given bank into the database (resulting in accounts and transactions).
    """
    logger.info("Importing %s", filename)
    with open(filename, encoding="ISO-8859-1") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')

        for row in reader:
            account_id = row["IBAN/BBAN"]
            account = _get_or_create_account(account_id, bank)

            date = datetime.datetime.strptime(row["Rentedatum"], "%Y-%m-%d").date()
            amount = decimal.Decimal(row["Bedrag"].replace(",", "."))
            name = " ".join(row["Naam tegenpartij"].split())

            description = " ".join(
                row["Omschrijving-1"].split() + row["Omschrijving-2"].split() + row["Omschrijving-3"].split())
            serial = int(row["Volgnr"].lstrip("0"))
            counter_account = row["Tegenrekening IBAN/BBAN"]
            balance = decimal.Decimal(row["Saldo na trn"].replace(",", "."))
            reference = row["Betalingskenmerk"]

            # Only create a new transaction if no identical transaction already exists!
            existing_transactions = services.find_transactions_by_attributes(account, date, serial, amount,
                                                                             name, counter_account,
                                                                             description)
            if existing_transactions:
                if len(existing_transactions) > 1:
                    raise ValueError("Database contains duplicate transactions!")
                else:
                    logger.debug("Skipping duplicate transaction: %s", existing_transactions[0])
            else:
                transaction = account_factory.create_transaction(account, date, amount, name, description, serial,
                                                                 counter_account, balance, reference)
                account.add_transaction(transaction)

            # mapping.map_transaction(transaction)


account_repository = infrastructure.repositories.account_repository.get_account_repository()
account_factory = infrastructure.repositories.account_repository.get_account_factory()
logger = logging.getLogger(__name__)


def _get_or_create_account(account_name, bank):
    account = account_repository.get_account_by_name(account_name)
    if account:
        pass  # assert bank.id == account.bank.id
    else:
        account = account_factory.create_account(account_name, bank)
    return account
