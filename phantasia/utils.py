import importlib
import uuid
import typing
import random
import string
from datetime import timezone
import datetime
import pathlib

from passlib.context import CryptContext
pwd_context = CryptContext(
    schemes=["argon2"],
    default="argon2",
)

def utcnow():
    dt = datetime.datetime.utcnow()
    return dt.replace(tzinfo=timezone.utc)


def import_from_module(path: str) -> typing.Any:
    if not path:
        raise ImportError("Cannot import null path!")
    if "." not in path:
        raise ImportError("Path is not in dot format!")
    split_path = path.split(".")
    identifier = split_path.pop(-1)
    module = importlib.import_module(".".join(split_path))
    return getattr(module, identifier)


# to_str is yoinked from Evennia.
def to_str(text, session=None):
    """
    Try to decode a bytestream to a python str, using encoding schemas from settings
    or from Session. Will always return a str(), also if not given a str/bytes.

    Args:
        text (any): The text to encode to bytes. If a str, return it. If also not bytes, convert
            to str using str() or repr() as a fallback.
        session (Session, optional): A Session to get encoding info from. Will try this before
            falling back to settings.ENCODINGS.

    Returns:
        decoded_text (str): The decoded text.

    Note:
        If `text` is already str, return it as is.
    """
    if isinstance(text, str):
        return text
    if not isinstance(text, bytes):
        # not a byte, convert directly to str
        try:
            return str(text)
        except Exception:
            return repr(text)

    default_encoding = (
        session.protocol_flags.get("ENCODING", "utf-8") if session else "utf-8"
    )
    try:
        return text.decode(default_encoding)
    except (LookupError, UnicodeDecodeError):
        for encoding in ["utf-8", "latin-1", "ISO-8859-1"]:
            try:
                return text.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                pass
        # no valid encoding found. Replace unconvertable parts with ?
        return text.decode(default_encoding, errors="replace")


def inherits_from(obj, parent):
    """
    Takes an object and tries to determine if it inherits at *any*
    distance from parent.

    Args:
        obj (any): Object to analyze. This may be either an instance or
            a class.
        parent (any): Can be either an instance, a class or the python
            path to the class.

    Returns:
        inherits_from (bool): If `parent` is a parent to `obj` or not.

    Notes:
        What differentiates this function from Python's `isinstance()` is the
        flexibility in the types allowed for the object and parent being compared.

    """

    if callable(obj):
        # this is a class
        obj_paths = ["%s.%s" % (mod.__module__, mod.__name__) for mod in obj.mro()]
    else:
        obj_paths = [
            "%s.%s" % (mod.__module__, mod.__name__) for mod in obj.__class__.mro()
        ]

    if isinstance(parent, str):
        # a given string path, for direct matching
        parent_path = parent
    elif callable(parent):
        # this is a class
        parent_path = "%s.%s" % (parent.__module__, parent.__name__)
    else:
        parent_path = "%s.%s" % (parent.__class__.__module__, parent.__class__.__name__)
    return any(1 for obj_path in obj_paths if obj_path == parent_path)


def is_iter(obj):
    """
    Checks if an object behaves iterably.

    Args:
        obj (any): Entity to check for iterability.

    Returns:
        is_iterable (bool): If `obj` is iterable or not.

    Notes:
        Strings are *not* accepted as iterable (although they are
        actually iterable), since string iterations are usually not
        what we want to do with a string.

    """
    if isinstance(obj, (str, bytes)):
        return False

    try:
        return iter(obj) and True
    except TypeError:
        return False


def make_iter(obj):
    """
    Makes sure that the object is always iterable.

    Args:
        obj (any): Object to make iterable.

    Returns:
        iterable (list or iterable): The same object
            passed-through or made iterable.

    """
    return not is_iter(obj) and [obj] or obj


# lazy load handler
_missing = object()


# Lazy property yoinked from evennia
class lazy_property:
    """
    Delays loading of property until first access. Credit goes to the
    Implementation in the werkzeug suite:
    http://werkzeug.pocoo.org/docs/utils/#werkzeug.utils.cached_property

    This should be used as a decorator in a class and in Evennia is
    mainly used to lazy-load handlers:

        ```python
        @lazy_property
        def attributes(self):
            return AttributeHandler(self)
        ```

    Once initialized, the `AttributeHandler` will be available as a
    property "attributes" on the object.

    """

    def __init__(self, func, name=None, doc=None):
        """Store all properties for now"""
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        """Triggers initialization"""
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
        obj.__dict__[self.__name__] = value
        return value


def fresh_uuid4(existing) -> uuid:
    """
    Given a list of UUID4s, generate a new one that's not already used.
    Yes, I know this is silly. UUIDs are meant to be unique by sheer statistic unlikelihood of a conflict.
    I'm just that afraid of collisions.
    """
    existing = set(existing)
    fresh_uuid = uuid.uuid4()
    while fresh_uuid in existing:
        fresh_uuid = uuid.uuid4()
    return fresh_uuid


def partial_match(match_text: str, candidates: typing.Iterable[typing.Any], key: callable = str,
        exact: bool = False, many_results: bool =False) -> typing.Optional[typing.Any]:
    """
    Given a list of candidates and a string to search for, does a case-insensitive partial name search against all
    candidates, preferring exact matches.

    Args:
        match_text (str): The string being searched for.
        candidates (list of obj): A list of any kind of object that key can turn into a string to search.
        key (callable): A callable that must return a string, used to do the search. this 'converts' the objects in the
            candidate list to strings.

    Returns:
        Any or None, or a list[Any]
    """
    mlow = match_text.lower()
    out = list()

    candidates_sorted = sorted((key(c).lower(), c) for c in candidates)

    for can_lower, candidate in candidates_sorted:
        if mlow == can_lower:
            if many_results:
                out.append(candidate)
            else:
                return candidate
        elif not exact and can_lower.startswith(mlow):
            if many_results:
                out.append(candidate)
            else:
                return candidate
    return out if many_results else None


def generate_name(prefix: str, existing, gen_length: int = 20) -> str:
    def gen():
        return f"{prefix}_{''.join(random.choices(string.ascii_letters + string.digits, k=gen_length))}"

    while (u := gen()) not in existing:
        return u


def get_server_pid() -> typing.Optional[int]:
    try:
        f = open("server.pid", mode="r")
        pid = int(f.read())
        return pid
    except:
        return None


def iequals(first: str, second: str):
    return str(first).lower() == str(second).lower()


class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def read_file(path: pathlib.Path) -> str:
    with path.open("r") as f:
        return f.read()