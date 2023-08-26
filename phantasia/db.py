from .utils import pwd_context
from sanic_jwt import initialize, exceptions
from surrealdb import Surreal

async def setup_db(app):
    db = Surreal("http://localhost:6000")
    await db.connect()
    await db.signin({"user": "root", "pass": "phantasia"})
    await db.use("phantasia", "phantasia")
    app.ctx.db = db

async def authenticate(request, *args, **kwargs):
    # Access form data
    username = request.form.get('username', None)
    password = request.form.get('password', None)

    if not username or not password:
        raise exceptions.AuthenticationFailed("Missing username or password.")

    result = await request.app.ctx.db.query("SELECT * FROM user WHERE string::lowercase(username) = $username",
                                            {"username": username.lower()})

    if not (results := result[0]["result"]):
        raise exceptions.AuthenticationFailed("User not found.")

    if len(results) != 1:
        raise exceptions.AuthenticationFailed("User not found.")

    user = results[0]
    if not pwd_context.verify(password, user["password"]):
        raise exceptions.AuthenticationFailed("Password is incorrect.")

    return user["username"].split(":", 1)[1]