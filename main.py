#!/usr/bin/env python

import argparse
import logging
import os

import application
import frontend


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description="Manage bank account information",
                                     epilog="Run with bokeh to use application in normal viewing mode: bokeh serve --show main.py")
    parser.add_argument("-i", "--import-rabobank-csv", metavar="rabobank_csv_file", type=str,
                        help="Import given Rabobank csv-file into the database")
    parser.add_argument("-e", "--export-data", type=str, metavar="native-directory",
                        help="Export database contents to accounts.csv, categories.csv and transactions.csv in given directory")
    parser.add_argument("-n", "--import-data", type=str, metavar="native-directory",
                        help="Import native csv-files from given directory into the database")
    args = parser.parse_args()
    return args


def main():
    logging.basicConfig(format='%(asctime)-15s %(levelname)-7s [%(name)s] %(message)s')
    logging.getLogger("").setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting application")

    args = parse_command_line_arguments()
    if args.import_data:
        application.initialize_application()
        logger.info(args)
        account_file = os.path.join(args.import_data, "accounts.csv")
        category_file = os.path.join(args.import_data, "categories.csv")
        transaction_file = os.path.join(args.import_data, "transactions.csv")
        logger.info("Importing native csv-files: %s, %s and %s", account_file, category_file, transaction_file)
        application.import_native_data(account_file, transaction_file, category_file)
        return

    if args.export_data:
        application.initialize_application()
        account_file = os.path.join(args.export_data, "accounts.csv")
        category_file = os.path.join(args.export_data, "categories.csv")
        transaction_file = os.path.join(args.export_data, "transactions.csv")
        logger.info("Exporting data to %s, %s and %s", account_file, transaction_file, category_file)
        application.export_native_data(account_file, transaction_file, category_file)
        return

    if args.import_rabobank_csv:
        application.initialize_application()
        logger.info("Importing rabobank csv-file: %s", args.import_rabobank_csv)
        application.import_rabobank_transactions([args.import_rabobank_csv])
        return

    frontend.main()


if __name__ == "__main__":
    main()
