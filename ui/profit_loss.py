import logging

import dateutil.relativedelta
from bokeh.events import PanEnd, Reset
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter, Title
from bokeh.plotting import figure

import application.services
import ui

MS_IN_24_DAYS = 24 * 24 * 60 * 60 * 1000

MS_IN_300_DAYS = 300 * 24 * 60 * 60 * 1000

logger = logging.getLogger(__name__)

_data = {}


def get_profit_loss_plot(figure_manager):
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

    source = ColumnDataSource(data=get_profit_loss_data(figure_manager.granularity))

    fig = figure(sizing_mode='stretch_width', plot_height=300, x_axis_type="datetime",
                 tools=[hover, "tap", "box_zoom", "wheel_zoom", "reset", "pan"])
    fig.title = Title(text="Income/expenses & profit/loss")
    fig.min_border_left = 80
    fig.min_border_right = 40
    fig.yaxis.formatter = NumeralTickFormatter(format="0,0")

    income_glyph = fig.vbar('date', name='income', top='income', width=24 * 24 * 60 * 60 * 1000, source=source,
                            color="lightgray")
    expenses_glyph = fig.vbar('date', top='expenses', width=24 * 24 * 60 * 60 * 1000, source=source, color="lightgray")
    profit_glyph = fig.vbar('date', top='profit', width=24 * 24 * 60 * 60 * 1000, source=source, line_alpha=0)
    loss_glyph = fig.vbar('date', top='loss', width=24 * 24 * 60 * 60 * 1000, source=source, color="#FF4040",
                          line_alpha=0)

    def on_pan(event):
        figure_manager.update_x_range(fig.x_range)

    fig.on_event(PanEnd, on_pan)
    fig.on_event(Reset, on_pan)
    figure_manager.register_figure(fig)

    _data['figure'] = fig
    _data['plots'] = [income_glyph, expenses_glyph, profit_glyph, loss_glyph]
    _data['source'] = source
    figure_manager.register_granularity_callback(set_granularity)

    return fig


def set_granularity(granularity):
    logger.info("Setting profit-loss granularity to: %s", granularity)
    data = get_profit_loss_data(granularity)
    _data['source'].data = data
    for plot in _data['plots']:
        if granularity == ui.FigureManager.TimeUnit.YEAR:
            plot.glyph.width = MS_IN_300_DAYS
        else:
            plot.glyph.width = MS_IN_24_DAYS


def get_profit_loss_data(granularity):
    date_list = application.services.get_transaction_date_range(day_nr=1)
    transactions_per_month = [
        application.services.get_transactions_between(month, month + dateutil.relativedelta.relativedelta(months=1))
        for month in date_list]
    income = []
    expenses = []
    for transaction_list in transactions_per_month:
        income.append(
            sum([t.amount for t in transaction_list if t.amount > 0 and not t.internal]))
        expenses.append(
            sum([t.amount for t in transaction_list if t.amount < 0 and not t.internal]))

    if granularity == ui.FigureManager.TimeUnit.YEAR:
        # Convert to year-data
        date_list = date_list[0::12]
        expenses_yearly = []
        income_yearly = []
        for year in range(len(date_list)):
            expenses_yearly.append(sum(expenses[year * 12:min((year + 1) * 12, len(expenses))]))
            income_yearly.append(sum(income[year * 12:min((year + 1) * 12, len(income))]))
        expenses = expenses_yearly
        income = income_yearly

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

    return {'date': date_list, 'income': income, 'expenses': expenses, 'profit': profit, 'loss': loss}
