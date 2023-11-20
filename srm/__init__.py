from flask import Flask

from .Core.Routes import core
from .Site.Routes import site

def create_app():
    app = Flask(__name__)

    app.register_blueprint(core)
    app.register_blueprint(site)

    return app