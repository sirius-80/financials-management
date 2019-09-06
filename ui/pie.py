import math
import pandas
from bokeh.layouts import row
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum

import application.services
import infrastructure


def get_pie_plot(figure_manager):
    source = ColumnDataSource(data=get_data())
    fig = figure(title="Subcategories", toolbar_location=None, tooltips="@category: €@amount{0,0}",
                 x_range=(-0.5, 1.0))
    pie = fig.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
              line_color="white", fill_color='color', legend='category', source=source)
    fig.legend.click_policy = "mute"
    fig.axis.axis_label = None
    fig.axis.visible = False
    fig.grid.grid_line_color = None

    def on_update(figure_manager):
        data = get_data(figure_manager.category, figure_manager.date_range[0], figure_manager.date_range[1])
        source.data = data

    figure_manager.register_category_callback(on_update)
    figure_manager.register_date_range_callback(on_update)

    return row(fig)


def get_data(parent_category=None, start_date=None, end_date=None):
    start_date = start_date or application.services.get_date_of_first_transaction()
    end_date = end_date or application.services.get_date_of_last_transaction()
    if parent_category:
        categories = parent_category.children or [parent_category]
    else:
        category_repository = infrastructure.Infrastructure.category_repository()
        categories = [c for c in category_repository.get_categories() if not c.parent]
    x = {}
    for category in categories:
        x[category.qualified_name] = abs(float(sum([t.amount for t in
                                                    application.services.get_transactions_for_category_between(
                                                        start_date,
                                                        end_date,
                                                        category)])))
    data = pandas.Series(x).reset_index(name='amount').rename(columns={'index': 'category'})
    data['angle'] = data['amount'] / data['amount'].sum() * 2 * math.pi
    if len(x) > 2:
        data['color'] = Category20c[len(x)]
    else:
        data['color'] = "#3182bd"
    return data
