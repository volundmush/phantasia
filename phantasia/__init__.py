from pathlib import Path

from .utils import import_from_module

from sanic import Sanic, response
from sanic_ext import render

phantasia_folder = Path(__file__).resolve().parent  # Get the absolute path of the current file

static = phantasia_folder / "static"
templates = phantasia_folder / "templates"

app = Sanic("phantasia")
app.ctx.template_info = dict()

app.config.TEMPLATING_ENABLE_ASYNC = True
app.config.TEMPLATING_PATH_TO_TEMPLATES = templates

config_file = Path("config.py").resolve()
if config_file.exists():
    app.update_config(config_file)
else:
    raise Exception("Cannot find config.py in <cwd>")

app.ctx.template_info["name"] = getattr(app.config, "SERVERNAME", "phantasia")

app.static("/static", static)


@app.route("/")
async def index(request):
    return await render("index.html", context=request.app.ctx.template_info)


@app.route("/initialContent")
async def initial_content(request):
    return await render("site.html", context=request.app.ctx.template_info)


@app.route("/site/login")
async def site_login(request):
    return await render("site/login.html", context=request.app.ctx.template_info)


@app.route("/site/home")
async def site_home(request):
    return await render("site/home.html", context=request.app.ctx.template_info)