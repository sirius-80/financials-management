import logging

from bokeh.events import PanEnd
from bokeh.models import ColumnDataSource, HoverTool, Span, NumeralTickFormatter
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
    data = get_balance_data()
    source = ColumnDataSource(data=data)
    fig = figure(sizing_mode='stretch_width', plot_height=300, x_axis_type="datetime",
                 tools=[hover, "tap", "box_zoom", "wheel_zoom", "reset", "pan"])
    fig.yaxis.formatter = NumeralTickFormatter(format="0,0")

    balance_plot = fig.line(x='date', y='balance', source=source, line_width=5, color="navy", alpha=0.5)
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

    fig.on_event(PanEnd, on_pan)
    figure_manager.register_figure(fig)

    return fig


def get_balance_data():
    date_list = application.services.get_transaction_date_range()
    balances = ui.get_balances(date_list)

    return {'date': date_list, 'balance': balances}
