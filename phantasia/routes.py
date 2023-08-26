from pathlib import Path
from sanic import Blueprint

from .utils import import_from_module, pwd_context

from sanic import response
from sanic_ext import render

from sanic_jwt import initialize, exceptions
from sanic_jwt.decorators import protected, inject_user

phantasia_folder = Path(__file__).resolve().parent  # Get the absolute path of the current file

static = phantasia_folder / "static"

bp = Blueprint("phantasia")

bp.static("/static", static)


@bp.route("/")
async def index(request):
    return await render("index.html", context=request.app.ctx.template_info)


@bp.route("/site")
async def site_get(request):
    return await render("site.html", context=request.app.ctx.template_info)


@bp.route("/site/<page_name>")
async def site_page_get(request, page_name):
    return await render(f"site/{page_name}.html", context=request.app.ctx.template_info)


@bp.post("/login")
async def handle_login(request):
    # Access form data
    username = request.form.get('username')
    password = request.form.get('password')

    result = await request.app.ctx.db.query("SELECT username,password FROM user WHERE string::lowercase(username) = $username",
                                            {"username": username.lower()})

    if not (results := result[0]["result"]):
        return response.redirect("/site/login?error=Invalid+username+or+password")

    if len(results) != 1:
        return response.redirect("/site/login?error=Invalid+username+or+password")

    user = results[0]
    if not pwd_context.verify(password, user["password"]):
        return response.redirect("/site/login?error=Invalid+username+or+password")

    # all good!
    # set the session cookie and redirect to the home page.


@bp.post("/register")
async def handle_register(request):
    # Access form data
    username = request.form.get('username')
    password = request.form.get('password')

    # first we must check for if a user with that name already exists...
    # if not, then we can create the user and log them in.

    result = await request.app.ctx.db.query("SELECT * FROM user WHERE string::lowercase(username) = $username",
                                            {"username": username.lower()})

    print(result)
    if result[0]["result"]:
        return response.redirect("/site/register?error=Username+already+exists")

    user = await request.app.ctx.db.create("user", {"username": username, "password": pwd_context.hash(password)})

    print(user)