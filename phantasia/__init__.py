from pathlib import Path

from .utils import import_from_module

from sanic import Sanic, response
from sanic_ext import render

from sanic_jwt import initialize, exceptions
from sanic_jwt.decorators import protected, inject_user
from .db import authenticate, setup_db

phantasia_folder = Path(__file__).resolve().parent  # Get the absolute path of the current file

templates = phantasia_folder / "templates"

app = Sanic("phantasia")

app.config.TEMPLATING_ENABLE_ASYNC = True
app.config.TEMPLATING_PATH_TO_TEMPLATES = templates

config_file = Path("config.py").resolve()
if config_file.exists():
    app.update_config(config_file)
else:
    raise Exception("Cannot find config.py in <cwd>")

jwt = initialize(app,
                 authenticate=authenticate,
                 claim_aud=app.config.HOST_NAME,
                 claim_iss=app.config.HOST_NAME,
                 claim_iat=True,
                 secret=app.config.JWT_SECRET,
                 cookie_set=True,
                 cookie_split=True,
                 cookie_access_token_name='token-header-payload',
                 cookie_domain=app.config.HOST_NAME)


app.ctx.template_info = dict()
app.ctx.template_info["name"] = getattr(app.config, "SERVERNAME", "phantasia")
app.ctx.template_info["nav_items"] = [
    {'path': '/site/home', 'label': 'Home'},
    {'path': '/site/login', 'label': 'Login'},
    {'path': '/site/register', 'label': 'Register'},
]

app.register_listener(setup_db, "before_server_start")

from . routes import bp
app.blueprint(bp)
