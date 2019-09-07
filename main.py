#!/usr/bin/env python

import argparse
import logging

from bokeh.io import curdoc

# Note that the repository packages need to be imported before anything else, in order for injection of the repository
# implementations in the domain to work
__import__("infrastructure.repositories.account_repository")
__import__("infrastructure.repositories.category_repository")

import application
import ui


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description="Manage bank account information",
                                     epilog="Run with bokeh to use application in normal viewing mode: bokeh serve --show main.py")
    parser.add_argument("-i", "--import-rabobank-csv", metavar="rabobank_csv_file", type=str,
                        help="Import given Rabobank csv-file into the database")
    parser.add_argument("-e", "--export-data", action="store_true",
                        help="Export database contents to accounts.csv, categories.csv and transactions.csv")
    parser.add_argument("-n", "--import-data", action="store_true",
                        help="Import given native csv-file into the database")
    args = parser.parse_args()
    print(args)
    return args


def main():
    logging.basicConfig(format='%(asctime)-15s %(levelname)-7s [%(name)s] %(message)s')
    logging.getLogger("").setLevel(logging.INFO)
    logger = logging.getLogger(__name__)

    args = parse_command_line_arguments()

    if args.import_data:
        account_file = "accounts.csv"
        category_file = "categories.csv"
        transaction_file = "transactions.csv"
        logger.info("Importing native csv-files: %s, %s and %s", account_file, category_file, transaction_file)
        application.import_native_data(account_file, transaction_file, category_file)
        return

    if args.export_data:
        account_file = "accounts.csv"
        category_file = "categories.csv"
        transaction_file = "transactions.csv"
        logger.info("Exporting data to %s, %s and %s", account_file, transaction_file, category_file)
        application.export_native_data(account_file, transaction_file, category_file)
        return

    application.initialize_application()

    if args.import_rabobank_csv:
        logger.info("Importing rabobank csv-file: %s", args.import_rabobank_csv)
        application.import_rabobank_transactions([args.import_rabobank_csv])
        return

    application.log_current_account_info()

    ui.plot_data_with_bokeh(curdoc())


main()
