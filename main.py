import infrastructure.repositories.category_repository
import infrastructure.repositories.account_repository
import application

if __name__ == "__main__":
    application.initialize_application()

    # Store changes in the database
    # infrastructure.repositories.get_database().connection.commit()

    account_repository = infrastructure.repositories.account_repository.get_account_repository()
    application.import_transactions(account_repository,
                                    infrastructure.repositories.account_repository.get_account_factory(),
                                    ["transacties-20190501-to-20190801.csv"])
    application.log_current_account_info(account_repository)
