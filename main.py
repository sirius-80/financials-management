import argparse
import logging

import infrastructure.repositories.category_repository
import infrastructure.repositories.account_repository
import application
import ui


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description="Manage bank account information",
                                     epilog="Run with bokeh to use application in normal viewing mode: bokeh serve --show main.py")
    parser.add_argument("-i", "--import-rabobank-csv", metavar="rabobank_csv_file", type=str,
                        help="Import given Rabobank csv-file into the database")
    args = parser.parse_args()
    print(args)
    return args


def main():
    logging.basicConfig(format='%(asctime)-15s %(levelname)-7s [%(name)s] %(message)s')
    logging.getLogger("").setLevel(logging.INFO)

    application.initialize_application()
    args = parse_command_line_arguments()

    if args.import_rabobank_csv:
        print(args.import_rabobank_csv)
        application.import_rabobank_transactions([args.import_rabobank_csv])
        infrastructure.repositories.get_database().connection.commit()

    account_repository = infrastructure.repositories.account_repository.get_account_repository()
    application.log_current_account_info(account_repository)

    ui.plot_data_with_bokeh()


main()
