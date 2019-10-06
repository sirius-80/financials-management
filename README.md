# financials-management

Simple web-based application to gain insight in financial situation, based on bank accounts and transactions.

# Usage
To import data (currently only Rabobank csv-files are supported):
```sh
./main.py --import-rabobank-csv CSV_A.csv
```

To use the application:
```sh
bokeh serve --show main.py
```

![Screenshot](docs/screenshot-financials-management.png?raw=true "Screenshot")