from flask import Flask
from flask.ext.lastuser import Lastuser
from flask.ext.assets import Environment, Bundle
from ._version import __version__

app = Flask(__name__)
assets = Environment(app)
lastuser = Lastuser()

css = Bundle('style.css', filters='cssmin', output='gen/all.css')

assets.register('css_site', css)


@app.context_processor
def inject_version():
    return dict(version = __version__,
                testing = app.config.get('LASTUSER_TEST'))

from . import views, models
