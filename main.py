import logging

import infrastructure.repositories.category_repository
import infrastructure.repositories.account_repository
import application
import ui


def main():
    logging.basicConfig(format='%(asctime)-15s %(levelname)-7s [%(name)s] %(message)s')
    logging.getLogger("").setLevel(logging.INFO)

    application.initialize_application()

    # Store changes in the database
    # infrastructure.repositories.get_database().connection.commit()

    account_repository = infrastructure.repositories.account_repository.get_account_repository()
    application.log_current_account_info(account_repository)

    ui.plot_data_with_bokeh()


main()
