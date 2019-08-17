import logging
import pprint

import dateutil
from bokeh.events import Tap, PanEnd, Reset
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HoverTool, TapTool, TableColumn, DateFormatter, NumberFormatter, \
    SelectEditor, DataTable, Select, WidgetBox, NumeralTickFormatter, Title
from bokeh.plotting import figure

import application.services
import infrastructure.repositories.account_repository
import infrastructure.repositories.category_repository
import ui

logger = logging.getLogger(__name__)


def get_category_plot(figure_manager):
    date_list = application.services.get_transaction_date_range()
    category_repository = infrastructure.Repositories.category_repository()
    account_repository = infrastructure.Repositories.account_repository()
    category = None
    amounts = [application.services.get_combined_amount_for_category_in_month(category, month) for month in date_list]
    settings = {'category': category,
                'granularity': ui.FigureManager.TimeUnit.MONTH,
                'transactions': []}

    amounts_source = ColumnDataSource(data={'date': date_list, 'amount': amounts})
    hover = HoverTool(
        tooltips=[
            ('Date', '@date{%F}'),
            ('Amount', '@amount{(0,0.00}')
        ],
        formatters={
            'date': 'datetime'
        },
        mode='vline'
    )
    fig = figure(sizing_mode='stretch_width', plot_height=300, x_axis_type="datetime",
                 tools=[hover, "tap", "box_zoom", "wheel_zoom", "reset", "pan"])
    fig.title = Title(text="Income/expenses per category")
    fig.min_border_left = 80
    fig.min_border_right = 40
    plot = fig.vbar('date', top='amount', width=24 * 24 * 60 * 60 * 1000, source=amounts_source)
    fig.yaxis.formatter = NumeralTickFormatter(format="0,0")
    fig.select(type=TapTool)

    columns = [
        TableColumn(field="date", title="Date", formatter=DateFormatter(), width=100),
        TableColumn(field="account", title="Account", width=150),
        TableColumn(field="amount", title="Amount", formatter=NumberFormatter(format='€ 0,0.00', text_align='right'),
                    width=100),
        TableColumn(field="name", title="Name"),
        TableColumn(field="category", title="Category",
                    editor=SelectEditor(options=["None"] + [str(c) for c in category_repository.get_categories()])),
        TableColumn(field="description", title="Description", width=800),
        TableColumn(field="counter_account", title="Counter account", width=200)
    ]
    transaction_data = dict(
        date=[],
        account=[],
        amount=[],
        category=[],
        name=[],
        description=[],
        counter_account=[]
    )
    transaction_source = ColumnDataSource(transaction_data)
    transactions_table = DataTable(source=transaction_source, columns=columns, fit_columns=True, editable=True,
                                   width=1500)

    def on_update_category(attr, old, new):
        logger.debug("on_update_category %s::%s => %s", attr, old, new)
        table_categories = new['category']
        if table_categories:
            logger.info("Update!")
            for transaction, category_qualified_name in zip(settings['transactions'], table_categories):
                if str(transaction.category) != category_qualified_name:
                    new_category = category_repository.get_category_by_qualified_name(category_qualified_name)
                    logger.info("Updating transaction category %s => %s", transaction, new_category)
                    transaction.update_category(new_category)
                    account_repository.save_transaction(transaction)
                    infrastructure.repositories.get_database().connection.commit()

    transactions_table.source.on_change('data', on_update_category)

    def on_selection_event(event):
        if amounts_source.selected.indices:
            update_transaction_table()
        else:
            clear_transaction_table()

    def clear_transaction_table():
        data = dict(
            date=[],
            account=[],
            amount=[],
            category=[],
            name=[],
            descr=[],
            counter_account=[]
        )
        settings['transactions'] = []
        transaction_source.data = data

    def update_transaction_table():
        index = amounts_source.selected.indices[0]
        start_date = amounts_source.data['date'][index]
        logger.debug("Selecting category '%s' and date %s", settings['category'], start_date)
        if settings['granularity'] == ui.FigureManager.TimeUnit.YEAR:
            end_date = start_date + dateutil.relativedelta.relativedelta(years=1)
        else:
            end_date = start_date + dateutil.relativedelta.relativedelta(months=1)
        logger.debug("Selecting transactions between %s and %s", start_date, end_date)
        selected_transactions = application.services.get_transactions_for_category_between(start_date, end_date,
                                                                                           category=category_repository.get_category_by_qualified_name(
                                                                                               settings['category']))
        settings['transactions'] = selected_transactions
        pprint.pprint(selected_transactions)
        data = dict()
        data['date'] = [t.date for t in selected_transactions]
        data['account'] = [t.account.name for t in selected_transactions]
        data['amount'] = [float(t.amount) for t in selected_transactions]
        data['name'] = [t.name for t in selected_transactions]
        data['category'] = [str(t.category) for t in selected_transactions]
        data['description'] = [t.description for t in selected_transactions]
        data['counter_account'] = [t.counter_account for t in selected_transactions]
        transaction_source.data = data

    fig.on_event(Tap, on_selection_event)

    def update_plot():
        data = dict()
        data['date'] = application.services.get_transaction_date_range(day_nr=1)
        data['amount'] = [application.services.get_combined_amount_for_category_in_month(
            category_repository.get_category_by_qualified_name(settings['category']), month) for month in date_list]
        if settings['granularity'] == ui.FigureManager.TimeUnit.YEAR:
            amounts_by_year = []
            for i in range(len(data['amount'])):
                if i % 12 == 0:
                    amounts_by_year.append(0)
                amounts_by_year[i // 12] += data['amount'][i]
            data['date'] = data['date'][0::12]
            data['amount'] = amounts_by_year
            plot.glyph.width = 300 * 24 * 60 * 60 * 1000
        else:
            plot.glyph.width = 24 * 24 * 60 * 60 * 1000
        fig.y_range.start = min(0, min(data['amount'])) - 0.1 * (max(data['amount']) - min(data['amount']))
        fig.y_range.end = max(data['amount']) + 0.1 * (max(data['amount']) - min(data['amount']))
        amounts_source.data = data

    def update_category(attrname, old, new):
        logger.debug("Callback %s: %s -> %s", attrname, str(old), str(new))
        settings['category'] = new
        update_plot()

    def update_date_range(attrname, old, new):
        logger.debug("Callback %s: %s -> %s", attrname, str(old), str(new))
        if new == "Month":
            settings['granularity'] = ui.FigureManager.TimeUnit.MONTH
        else:
            settings['granularity'] = ui.FigureManager.TimeUnit.YEAR

        figure_manager.set_granularity(settings['granularity'])
        update_plot()

    category_selector = Select(title="Category", options=["None"] + [str(c) for c in
                                                                     category_repository.get_categories()], width=200)
    category_selector.on_change('value', update_category)
    date_range_selector = Select(title="Granularity", options=["Month", "Year"], width=200)
    date_range_selector.on_change('value', update_date_range)
    inputs = WidgetBox(category_selector, date_range_selector)

    def on_pan(event):
        figure_manager.update_x_range(fig.x_range)

    fig.on_event(PanEnd, on_pan)
    fig.on_event(Reset, on_pan)

    figure_manager.register_figure(fig)
    return column(fig, row(inputs, transactions_table, sizing_mode='stretch_width'), sizing_mode='stretch_width')
