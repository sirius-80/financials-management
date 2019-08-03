import logging
from enum import Enum

from bokeh.io import curdoc, show
from bokeh.layouts import column
from bokeh.models import Range1d

import application.services
from ui.balances import get_balance_plot
from ui.categories import get_category_plot
from ui.profit_loss import get_profit_loss_plot

logger = logging.getLogger(__name__)


def get_balances(date_list):
    balances = []
    for date in date_list:
        balances.append(application.services.get_combined_balance_at(date))
    return balances


def plot_data_with_bokeh():
    range_manager = RangeManager()
    balance_plot = get_balance_plot(range_manager)
    profit_loss_plot = get_profit_loss_plot(range_manager)
    amount_per_category_plot = get_category_plot(range_manager)

    curdoc().add_root(column(balance_plot, profit_loss_plot, amount_per_category_plot))


class RangeManager:
    class TimeUnit(Enum):
        MONTH = 1
        YEAR = 2

    def __init__(self):
        self.x_range = None
        self.figures = []
        self.granularity = self.TimeUnit.MONTH

    def update_x_range(self, x_range):
        self.x_range = x_range
        for figure in self.figures:
            logger.debug("Updating range of figure %s: %s .. %s", figure, x_range.start, x_range.end)
            figure.x_range.start = x_range.start
            figure.x_range.end = x_range.end

    def register_figure(self, figure):
        logger.debug("Registering figure: %s", figure)
        self.update_x_range(figure.x_range)
        self.figures.append(figure)
