from bokeh.io import curdoc
from bokeh.layouts import column

from ui.balances import get_balance_plot
from ui.categories import get_category_plot
import application.services


def get_balances(date_list):
    balances = []
    for date in date_list:
        balances.append(application.services.get_combined_balance_at(date))
    return balances


def plot_data_with_bokeh():
    balance_plot = get_balance_plot()
    amount_per_category_plot = get_category_plot()

    curdoc().add_root(column(balance_plot, amount_per_category_plot))
