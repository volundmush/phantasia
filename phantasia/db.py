from .utils import pwd_context
from sanic_jwt import initialize, exceptions
from surrealdb import Surreal


async def setup_db(app):
    db = Surreal("http://localhost:6000")
    await db.connect()
    await db.signin({"user": "root", "pass": "phantasia"})
    await db.use("phantasia", "phantasia")
    app.ctx.db = db


async def retrieve_user(request, payload, *args, **kwargs):
    if not payload:
        return None
    result = await request.app.ctx.db.query("SELECT * FROM user WHERE id = $id", {"id": f"user:{payload['user_id']}"})
    if not (results := result[0]["result"]):
        raise exceptions.AuthenticationFailed("User not found.")

    if len(results) != 1:
        raise exceptions.AuthenticationFailed("User not found.")

    return results[0]


async def authenticate(request, *args, **kwargs):
    # Access form data
    username = request.json.get('username', None)
    password = request.json.get('password', None)

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

    out = {
        "user_id": user["id"].split(":", 1)[1],
        "username": user["username"]
    }

    return out