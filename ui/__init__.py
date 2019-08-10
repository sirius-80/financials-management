import logging
from enum import Enum

from bokeh.io import curdoc
from bokeh.layouts import column

import application.services
from ui.balances import get_balance_plot
from ui.categories import get_category_plot
from ui.profit_loss import get_profit_loss_plot

logger = logging.getLogger(__name__)


def get_balances(date_list):
    return [application.services.get_combined_balance_at(date) for date in date_list]


def plot_data_with_bokeh():
    figure_manager = FigureManager()
    balance_plot = get_balance_plot(figure_manager)
    profit_loss_plot = get_profit_loss_plot(figure_manager)
    amount_per_category_plot = get_category_plot(figure_manager)

    curdoc().add_root(column(balance_plot, profit_loss_plot, amount_per_category_plot, sizing_mode='stretch_width'))


class FigureManager:
    class TimeUnit(Enum):
        MONTH = 1
        YEAR = 2

    def __init__(self):
        self.x_range = None
        self.figures = []
        self.granularity = self.TimeUnit.MONTH
        self.granularity_callbacks = []

    def set_granularity(self, granularity):
        self.granularity = granularity
        for cb in self.granularity_callbacks:
            try:
                cb(granularity)
            except:
                pass

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

    def register_granularity_callback(self, cb):
        self.granularity_callbacks.append(cb)
