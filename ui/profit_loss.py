import logging

import dateutil.relativedelta
from bokeh.events import PanEnd
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure

import application.services
import infrastructure.repositories.account_repository
import infrastructure.repositories.category_repository

logger = logging.getLogger(__name__)

_data = {}


def get_profit_loss_plot(range_manager):
    date_list = application.services.get_transaction_date_range(day_nr=1)
    category_repository = infrastructure.repositories.category_repository.get_category_repository()

    transactions_per_month = [
        application.services.get_transactions_between(month, month + dateutil.relativedelta.relativedelta(months=1))
        for month in date_list]

    internal_transaction_category = category_repository.get_category_by_qualified_name("Overboekingen")
    # Filter-out internal transactions
    for transaction_list in transactions_per_month:
        internal_transactions = [t for t in transaction_list if t.category == internal_transaction_category]
        [transaction_list.remove(t) for t in internal_transactions]

    income = []
    expenses = []
    for transaction_list in transactions_per_month:
        income.append(sum([t.amount for t in transaction_list if t.amount > 0]))
        expenses.append(sum([t.amount for t in transaction_list if t.amount < 0]))

    profit = []
    loss = []
    for money_in, money_out in zip(income, expenses):
        profit_loss = money_in + money_out
        if profit_loss > 0:
            profit.append(profit_loss)
            loss.append(0)
        else:
            loss.append(profit_loss)
            profit.append(0)

    source = ColumnDataSource(
        data={'date': date_list, 'income': income, 'expenses': expenses, 'profit': profit, 'loss': loss})
    hover = HoverTool(
        tooltips=[
            ('Date', '@date{%F}'),
            ('Income', '@income{(0,0.00}'),
            ('Expenses', '@expenses{(0,0.00}'),
            ('Profit', '@profit{(0,0.00}'),
            ('Loss', '@loss{(0,0.00}')
        ],
        formatters={
            'date': 'datetime'
        },
        mode='vline',
        # This binds the hover-tool only to the 'income' glyph, so that only a single hoverbox shows up
        names=["income"]
    )
    fig = figure(plot_width=1900, plot_height=300, x_axis_type="datetime",
                             tools=[hover, "tap", "box_zoom", "wheel_zoom", "reset", "pan"])
    income_glyph = fig.vbar('date', name='income', top='income', width=24 * 24 * 60 * 60 * 1000, source=source,
                            color="lightgray")
    expenses_glyph = fig.vbar('date', top='expenses', width=24 * 24 * 60 * 60 * 1000, source=source, color="lightgray")
    profit_glyph = fig.vbar('date', top='profit', width=24 * 24 * 60 * 60 * 1000, source=source, line_alpha=0)
    loss_glyph = fig.vbar('date', top='loss', width=24 * 24 * 60 * 60 * 1000, source=source, color="#FF4040",
                          line_alpha=0)

    def on_pan(event):
        range_manager.update_x_range(fig.x_range)

    fig.on_event(PanEnd, on_pan)
    range_manager.register_figure(fig)

    _data['figure'] = fig
    return column(fig)
