import datetime
import pprint

from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import WidgetBox, ColumnDataSource, DataTable, TableColumn, TapTool, HoverTool, Span
from bokeh.plotting import figure


def get_dates(last_date, day_nr=20):
    dates = []
    for year in range(2012, last_date.year + 1):
        for month in range(1, 13):
            d = datetime.datetime(year, month, day_nr).date()
            dates.append(d)
            if d > last_date:
                print("Stopping at date %s" % d)
                break

    return dates


def get_saldi_plot(dates, saldi):
    data = {'date': dates,
            'saldo': saldi}
    saldi_source = ColumnDataSource(data=data)
    hover = HoverTool(
        tooltips=[
            ('Date', '@date{%F}'),
            ('Saldo', '@saldo{(0,0.00}')
        ],
        formatters={
            'date': 'datetime'
        },
        mode='vline'
    )
    plot = figure(plot_width=1900, plot_height=300, x_axis_type="datetime",
                  tools=[hover, "tap", "box_zoom", "wheel_zoom", "reset", "pan"])
    plot.line(x='date', y='saldo', source=saldi_source, line_width=5, color="navy", alpha=0.5)
    # plot.circle(dates, plot, color="navy", alpha=0.5)
    # plot.y_range = Range1d(0, max(saldi))
    zero_line = Span(location=0, dimension="width", line_color="black", line_dash="dashed", line_width=3)
    plot.add_layout(zero_line)
    min_line = Span(location=min(saldi), dimension="width", line_color="red", line_dash="dashed", line_width=3)
    plot.add_layout(min_line)
    max_line = Span(location=max(saldi), dimension="width", line_color="green", line_dash="dashed", line_width=3)
    plot.add_layout(max_line)
    return plot


def get_category_plot(bank, category):
    dates = get_dates(bank.get_last_date(), 1)
    amounts = [bank.get_combined_amount_at(None, month) for month in dates]
    settings = {'category': None,
                'granularity': "Month"}

    data = {'date': dates,
            'amount': amounts}
    amounts_source = ColumnDataSource(data=data)
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
    fig = figure(plot_width=1900, plot_height=300, x_axis_type="datetime",
                 tools=[hover, "tap", "box_zoom", "wheel_zoom", "reset", "pan"])
    plot = fig.vbar('date', top='amount', width=24*24*60*60*1000, source=amounts_source)
    fig.select(type=TapTool)

    columns = [
        TableColumn(field="date", title="Date", formatter=DateFormatter()),
        TableColumn(field="account", title="Account"),
        TableColumn(field="amount", title="Amount", formatter=NumberFormatter(format='€ 0,0.00', text_align='right')),
        TableColumn(field="name", title="Name"),
        TableColumn(field="category", title="Category", editor=SelectEditor(options=[str(c) for c in category_repo.get_all_categories()])),
        TableColumn(field="descr", title="Description"),
        TableColumn(field="counter_account", title="Counter account")
    ]
    transaction_data = dict(
        date=[],
        account=[],
        amount=[],
        category=[],
        name=[],
        descr=[],
        counter_account=[]
    )
    transaction_source = ColumnDataSource(transaction_data)
    transactions_table = DataTable(source=transaction_source, columns=columns, width=1900, editable=True)

    def on_update_category(attr, old, new):
        print("on_update_category", attr, "::", old, "=>", new)
        #TODO: Keep old_data somewhere, as old == new always for single-cell updates
        # Find the change (only in category)
        old_cats = old['category']
        new_cats = new['category']
        print(old_cats, new_cats)
        if not old_cats or not new_cats or len(old_cats) != len(new_cats):
            print("No change")
        else:
            print("Update!")
            index = 0
            for original, update in zip(old_cats, new_cats):
                if original != update:
                    print("Updated index %d (%s => %s)" % (index, original, update))
                    break
                index += 1

    transactions_table.source.on_change('data', on_update_category)

    def selection_event(event):
        if amounts_source.selected.indices:
            index = amounts_source.selected.indices[0]
            start_date = amounts_source.data['date'][index]
            print("Selecting category and date", settings['category'], start_date)
            if settings['granularity'] == "Year":
                end_date = start_date + dateutil.relativedelta.relativedelta(years=1)
            else:
                end_date = start_date + dateutil.relativedelta.relativedelta(months=1)
            print("Selecting transactions between", start_date, end_date)
            selected_transactions = bank.get_transactions_between(start_date, end_date, category=settings['category'])
            pprint.pprint(selected_transactions)
            transaction_data = dict()
            transaction_data['date'] = [t.date for t in selected_transactions]
            transaction_data['account'] = [t.account for t in selected_transactions]
            transaction_data['amount'] = [t.amount for t in selected_transactions]
            transaction_data['name'] = [t.name for t in selected_transactions]
            transaction_data['category'] = [str(t.category) for t in selected_transactions]
            transaction_data['descr'] = [t.description for t in selected_transactions]
            transaction_data['counter_account'] = [t.counter_account for t in selected_transactions]
            transaction_source.data = transaction_data
        else:
            print("Deselection")
            transaction_data = dict(
                date=[],
                account=[],
                amount=[],
                category=[],
                name=[],
                descr=[],
                counter_account=[]
            )
            transaction_source.data = transaction_data
    fig.on_event(Tap, selection_event)

    def update_plot():
        if settings['granularity'] == "Year":
            dates = get_dates(bank.get_last_date(), 1)[0::12]
            plot.glyph.width = 300*24*60*60*1000
        else:
            dates = get_dates(bank.get_last_date(), 1)
            plot.glyph.width = 24*24*60*60*1000

        amounts = [bank.get_combined_amount_at(settings['category'], month) for month in get_dates(bank.get_last_date(), 1)]
        if settings['granularity'] == "Year":
            amounts_by_year = []
            for i in range(len(amounts)):
                if i % 12 == 0:
                    amounts_by_year.append(0)
                amounts_by_year[i // 12] += amounts[i]
            amounts = amounts_by_year
        amounts_source.data['amount'] = amounts
        amounts_source.data['date'] = dates

    def update_category(attrname, old, new):
        print("Callback %s: %s -> %s" % (attrname, str(old), str(new)))
        settings['category'] = category_repo.get_by_name(new)
        update_plot()

    def update_date_range(attrname, old, new):
        print("Callback %s: %s -> %s" % (attrname, str(old), str(new)))
        settings['granularity'] = new
        update_plot()

    category_selector = Select(title="Category", options=[(str(c), str(c)) for c in CategoryRepository().get_all_categories()])
    category_selector.on_change('value', update_category)
    date_range_selector = Select(title="Granularity", options=["Month", "Year"])
    date_range_selector.on_change('value', update_date_range)
    inputs = WidgetBox(category_selector, date_range_selector)

    return column(fig, inputs, transactions_table)


def plot_saldi_bokeh(dates, saldi, bank, category):
    saldi_plot = get_saldi_plot(dates, saldi)
    category_plot = get_category_plot(bank, category)
    curdoc().add_root(column(saldi_plot, category_plot))

