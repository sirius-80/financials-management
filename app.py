#!/usr/bin/env python

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import server_document
from bokeh.server.server import Server
from bokeh.util.browser import view
from jinja2 import FileSystemLoader, Environment
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler

import ui


# TODO: Base on https://github.com/bokeh/bokeh/blob/0.12.4/examples/howto/server_embed/tornado_embed.py


class IndexHandler(RequestHandler):
    def get(self):
        template = env.get_template('embed.html')
        script = server_document(url='http://localhost:5006/bkapp')
        self.write(template.render(script=script))


def modify_doc(doc):
    ui.plot_data_with_bokeh(doc)


if __name__ == "__main__":
    env = Environment(loader=FileSystemLoader('templates'))
    bokeh_app = Application(FunctionHandler(modify_doc))
    io_loop = IOLoop.current()
    server = Server({'/bkapp': bokeh_app}, io_loop=io_loop, extra_patterns=[('/', IndexHandler)])
    server.start()
    io_loop.add_callback(view, 'http://localhost:5006/')
    io_loop.start()
    # app.run(debug=True)
