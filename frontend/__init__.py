from datetime import datetime
import logging
from decimal import Decimal

from attr import dataclass
from flask import Flask, request
from flask_restful import Resource, Api
from json import dumps
from flask_cors import CORS

import application.services
from domain.account_management.model.category import category_repository
from domain.account_management.model.account import account_repository

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
api = Api(app)


class Combined:
    def __init__(self, date, balance, income, expenses, profit, loss, category_amount):
        self.date = date
        self.balance = balance
        self.income = income
        self.expenses = expenses
        self.profit = profit
        self.loss = loss
        self.category_amount = category_amount


class Balance:
    def __init__(self, date, amount):
        self.date = date
        self.amount = amount


@dataclass
class Category:
    id: str
    name: str


# class Category:
#     def __init__(self, id, name):
#         self.id = id
#         self.name = name


@dataclass
class Transaction:
    id: str
    date: datetime.date
    account: str
    amount: Decimal
    name: str
    category: Category
    description: str
    counter_account: str
    internal: bool


@app.route('/categories')
def get_categories():
    categories = [Category(0, "None").__dict__] + [Category(cat.id, cat.qualified_name).__dict__ for cat in
                                                   category_repository().get_categories()]
    response = app.response_class(dumps(categories, default=str),
                                  mimetype='application/json')
    return response


@app.route('/categories/<string:category_id>')
def get_category_data(category_id):
    mode = request.args.get('mode', 'monthly')
    category = category_repository().get_category(category_id)
    date_list = application.services.get_transaction_date_range(day_nr=1, mode=mode)
    monthly_amounts = [application.services.get_combined_amount_for_category(category, month, mode) for
                       month in date_list]
    response = app.response_class(
        response=dumps(
            [Balance(date, amount).__dict__ for (date, amount) in zip(date_list, monthly_amounts)], default=str),
        mimetype='application/json'
    )
    return response


@app.route('/combined_categories/<string:parent_id>')
def get_combined_category_data_for_period(parent_id=None):
    try:
        start = request.args.get('start', None)
        start_date = datetime.fromtimestamp(int(float(start) / 1000)).date()
    except ValueError:
        start_date = application.services.get_date_of_first_transaction()

    try:
        end = request.args.get('end', None)
        end_date = datetime.fromtimestamp(int(float(end) / 1000)).date()
    except ValueError:
        end_date = application.services.get_date_of_last_transaction()

    logger.info("Returning transaction-date from %s to %s", start_date, end_date)
    parent_category = category_repository().get_category(parent_id) or None

    if parent_category:
        categories = parent_category.children or [parent_category]
    else:
        categories = [c for c in category_repository().get_categories() if not c.parent]

    def get_category_amount(cat):
        cat_data = {
            'name': cat.name,
            'value': abs(float(sum(
                [t.amount for t in application.services.get_transactions_for_category(start_date, end_date, cat)])))}

        if cat.children:
            cat_data['children'] = []
            for child_cat in cat.children:
                cat_data['children'].append(get_category_amount(child_cat))
        return cat_data

    data = []
    for category in categories:
        data.append(get_category_amount(category))
    response = app.response_class(
        response=dumps(data, default=str),
        mimetype='application/json'
    )
    return response


@app.route('/combined')
def get_combined_data():
    mode = request.args.get('mode', 'monthly')
    category_id = request.args.get('category', None)
    category = category_repository().get_category(category_id)
    date_list = application.services.get_transaction_date_range(mode=mode)
    balance_list = [application.services.get_combined_balance_at(date) for date in date_list]
    income, expenses, profit, loss = application.services.get_income_expenses_profit_loss(date_list, mode=mode)
    category_amounts = [application.services.get_combined_amount_for_category(category, d, mode) for d in date_list]
    response = app.response_class(
        response=dumps(
            [Combined(date, balance, income, expenses, profit, loss, category_amount).__dict__ for
             (date, balance, income, expenses, profit, loss, category_amount) in
             zip(date_list, balance_list, income, expenses, profit, loss, category_amounts)],
            default=str),
        mimetype='application/json'
    )
    return response


@app.route('/transactions')
def get_transactions():
    try:
        start = request.args.get('start', None)
        start_date = datetime.fromtimestamp(int(float(start) / 1000)).date()
    except (ValueError, TypeError):
        start_date = application.services.get_date_of_first_transaction()

    try:
        end = request.args.get('end', None)
        end_date = datetime.fromtimestamp(int(float(end) / 1000)).date()
    except (ValueError, TypeError):
        end_date = application.services.get_date_of_last_transaction()

    transactions = application.services.get_transactions(start_date, end_date)
    response = app.response_class(
        response=dumps(
            [Transaction(t.id, t.date, t.account.name, t.amount, t.name,
                         t.category and Category(t.category.id, t.category.qualified_name).__dict__ or None,
                         t.description, t.counter_account, t.internal).__dict__
             for t in transactions],
            default=str
        ),
        mimetype='application/json'
    )
    return response


@app.route('/transactions/<string:transaction_id>/set_category', methods=['PUT'])
def set_category(transaction_id):
    category_id = request.json.get('categoryId')
    category = category_repository().get_category(category_id)
    transaction = account_repository().get_transaction(transaction_id)
    logger.info('Setting category of transaction id %s to %s', transaction, category)
    transaction.update_category(category)
    # TODO: Fix threading issue!!! account_repository().save_transaction(transaction)
    return app.response_class(
        response=dumps(Transaction(transaction.id, transaction.date, transaction.account.name, transaction.amount,
                                   transaction.name, transaction.category and Category(transaction.category.id,
                                                                                       transaction.category.qualified_name).__dict__ or None,
                                   transaction.description, transaction.counter_account,
                                   transaction.internal).__dict__, default=str),
        mimetype='application/json'
    )


def main():
    app.run(port='5002')
