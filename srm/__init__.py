from flask import Flask
from threading import Thread
from werkzeug.serving import make_server, BaseWSGIServer
from .Core.Routes import core
from .Site.Routes import site
import webview
import time
import logging


class ServerThread(Thread):
    def __init__(self, app):
        Thread.__init__(self)
        self.srv = make_server('127.0.0.1', 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print('starting server')
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

import logging



def create_app():
    app = Flask(__name__)
    app.register_blueprint(core)
    app.register_blueprint(site)
    app.config['SERVER_NAME'] = '127.0.0.1:5000'

    # Logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)

    server = ServerThread(app)
    server.start()

    time.sleep(1)  

    webview.create_window('Smart Route Maker', 'http://127.0.0.1:5000')
    webview.start()

    server.shutdown()

    return app

#old:
"""
from flask import Flask

from .Core.Routes import core
from .Site.Routes import site

def create_app():
    app = Flask(__name__)

    app.register_blueprint(core)
    app.register_blueprint(site)

    return app
"""