from bokeh.models import ColumnDataSource, HoverTool, Span
from bokeh.plotting import figure

import application.services
import ui


def get_balance_plot():
    date_list = application.services.get_transaction_date_range()
    balances = ui.get_balances(date_list)
    data = {'date': date_list,
            'saldo': balances}
    source = ColumnDataSource(data=data)
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
    plot.line(x='date', y='saldo', source=source, line_width=5, color="navy", alpha=0.5)
    zero_line = Span(location=0, dimension="width", line_color="black", line_dash="dashed", line_width=3)
    plot.add_layout(zero_line)
    min_line = Span(location=min(balances), dimension="width", line_color="red", line_dash="dashed", line_width=3)
    plot.add_layout(min_line)
    max_line = Span(location=max(balances), dimension="width", line_color="green", line_dash="dashed", line_width=3)
    plot.add_layout(max_line)
    return plot
