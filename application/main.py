import logging

import infrastructure
from application import rabo_csv_importer

RABOBANK_TWENTE_OOST = "Rabobank Twente Oost"
logger = logging.getLogger(__name__)


def import_transactions(account_repository, account_factory):
    bank = account_repository.get_bank_by_name(RABOBANK_TWENTE_OOST)
    if not bank:
        bank = account_factory.create_bank(RABOBANK_TWENTE_OOST)

    # for csv in ["transacties-20190101-to-20190719.csv", "transacties-20190501-to-20190725.csv"]:
    for csv in ["transacties-20120101-to-20190430.csv", "transacties-20190501-to-20190725.csv"]:
        rabo_csv_importer.import_transactions_csv(csv, bank)


if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(levelname)-7s [%(name)s] %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.getLogger("").setLevel(logging.DEBUG)

    # TODO: Link to cmd-line parameter?
    infrastructure.repositories.account_repository.enable_cache()

    repo = infrastructure.repositories.account_repository.get_account_repository()
    factory = infrastructure.repositories.account_repository.get_account_factory()

    if not repo.get_accounts():
        import_transactions(repo, factory)

    logger.debug("accounts: %s", repo.get_accounts())
    for account in repo.get_accounts():
        last_date = account.get_last_transaction_date()
        logger.warning("Account: %s (%s): %s => € %8s", account.name, account.id, last_date,
                    account.get_last_transaction_at_or_before(last_date).balance_after)

    infrastructure.repositories.get_database().connection.commit()
