import logging

from bokeh.events import PanEnd, Reset
from bokeh.models import ColumnDataSource, HoverTool, Span, NumeralTickFormatter, Title
from bokeh.plotting import figure

import application.services
import ui

logger = logging.getLogger(__name__)


def get_balance_plot(figure_manager):
    hover = HoverTool(
        tooltips=[
            ('Date', '@date{%F}'),
            ('Balance', '@balance{(0,0.00}')
        ],
        formatters={
            'date': 'datetime'
        },
        mode='vline'
    )
    data = get_balance_data(figure_manager.first_date_of_month)
    source = ColumnDataSource(data=data)
    fig = figure(sizing_mode='stretch_width', plot_height=300, x_axis_type="datetime",
                 tools=[hover, "tap", "box_zoom", "wheel_zoom", "reset", "pan"], name='balance')
    fig.yaxis.formatter = NumeralTickFormatter(format="0,0")

    balance_plot = fig.line(x='date', y='balance', source=source, line_width=5, color="navy", alpha=0.5)
    fig.title = Title(text="Account balance")
    fig.min_border_left = 80
    fig.min_border_right = 40
    zero_line = Span(location=0, dimension="width", line_color="black", line_dash="dashed", line_width=3)
    fig.add_layout(zero_line)
    min_line = Span(location=min(data['balance']), dimension="width", line_color="red", line_dash="dashed",
                    line_width=3)
    fig.add_layout(min_line)
    max_line = Span(location=max(data['balance']), dimension="width", line_color="green", line_dash="dashed",
                    line_width=3)
    fig.add_layout(max_line)

    def on_pan(event):
        figure_manager.update_x_range(fig.x_range)

    def first_date_of_month_update(granularity, first_date_of_month):
        logger.info("Updating date range: %s", first_date_of_month)
        data = get_balance_data(first_date_of_month)
        source.data = data

    fig.on_event(PanEnd, on_pan)
    fig.on_event(Reset, on_pan)

    figure_manager.register_figure(fig)
    figure_manager.register_first_date_of_month_callback(first_date_of_month_update)

    return fig


def get_balance_data(first_date_of_month):
    date_list = application.services.get_transaction_date_range(day_nr=first_date_of_month)
    balances = ui.get_balances(date_list)

    return {'date': date_list, 'balance': balances}
