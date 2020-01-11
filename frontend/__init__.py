from datetime import datetime
import logging

from flask import Flask, request
from flask_restful import Resource, Api
from json import dumps
from flask_cors import CORS

import application.services
from domain.account_management.model.category import category_repository


logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
api = Api(app)


class Combined:
    def __init__(self, date, balance, income, expenses, profit, loss):
        self.date = date
        self.balance = balance
        self.income = income
        self.expenses = expenses
        self.profit = profit
        self.loss = loss


class Balance:
    def __init__(self, date, amount):
        self.date = date
        self.amount = amount


class Category:
    def __init__(self, id, name):
        self.id = id
        self.name = name


@app.route('/categories')
def get_categories():
    categories = [Category(0, "None selected")] + [Category(cat.id, cat.qualified_name).__dict__ for cat in
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
        start_date = datetime.fromtimestamp(int(float(start)/1000)).date()
    except ValueError:
        start_date = application.services.get_date_of_first_transaction()

    try:
        end = request.args.get('end', None)
        end_date = datetime.fromtimestamp(int(float(end)/1000)).date()
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
    date_list = application.services.get_transaction_date_range(mode=mode)
    balance_list = [application.services.get_combined_balance_at(date) for date in date_list]
    income, expenses, profit, loss = application.services.get_income_expenses_profit_loss(date_list, mode=mode)
    response = app.response_class(
        response=dumps(
            [Combined(date, balance, income, expenses, profit, loss).__dict__ for
             (date, balance, income, expenses, profit, loss) in
             zip(date_list, balance_list, income, expenses, profit, loss)],
            default=str),
        mimetype='application/json'
    )
    return response


def main():
    app.run(port='5002')
