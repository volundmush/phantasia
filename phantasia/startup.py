#!/usr/bin/env python
import os
import asyncio
import setproctitle
import pickle
import logging
import signal
import sys
from logging.handlers import TimedRotatingFileHandler

from phantasia.utils import import_from_module


def main(setup_only=False):
    """
    The big kahuna that starts everything off.
    """

    # Install Rich as the traceback handler.
    from rich.traceback import install as install_tb
    install_tb(show_locals=True)

    # Retrieve environment variables and act upon them.
    env = os.environ.copy()
    if "MUDFORGE_PROFILE" in env:
        os.chdir(env["MUDFORGE_PROFILE"])
    sys.path.insert(0, os.getcwd())

    from server.conf import settings
    mudforge.CONFIG = settings

    # Sets the process name to something more useful than "python"
    setproctitle.setproctitle(settings.NAME)

    # aiomisc handles logging but we'll help it along with some better settings.
    log_handler = TimedRotatingFileHandler(filename=settings.SERVER_LOG_FILE, encoding="utf-8", utc=True,
                                           when="midnight", interval=1, backupCount=14)
    formatter = logging.Formatter(fmt=f"[%(asctime)s] %(message)s", datefmt="%x %X")
    log_handler.setFormatter(formatter)

    # The process will maintain a .pid file while it runs.
    pidfile = f"server.pid"

    for k, v in settings.HOOKS.items():
        for p in v:
            mudforge.HOOKS[k].append(import_from_module(p))

    for func in mudforge.HOOKS["early_launch"]:
        func()

    if setup_only:
        return

    copyover_data = None
    if os.path.exists("copyover.pickle"):
        with open("copyover.pickle", mode="rb") as f:
            try:
                copyover_data = pickle.load(f)
            except Exception as err:
                os.remove("copyover.pickle")
                raise
            os.remove("copyover.pickle")
            pid = copyover_data.pop("pid", None)
            if pid != os.getpid():
                raise Exception("Invalid copyover data! Server going down.")
    if not copyover_data:
        logging.info(f"Beginning Cold Start")
        for func in mudforge.HOOKS["cold_start"]:
            func()
    else:
        logging.info(f"Copyover Data detected.")


    # This context manager will ensure that the .pid stays write-locked as long as the process is running.
    with open(pidfile, "w") as pid_f:
        # immediately write the process ID to the .pid and flush it so it's readable.
        pid_f.write(str(os.getpid()))
        pid_f.flush()
        try:
            # Import and initialize classes and services from settings.
            empty = dict()
            for k, v in settings.CLASSES.items():
                mudforge.CLASSES[k] = import_from_module(v)
            for k, v in settings.SERVICES.items():
                mudforge.SERVICES[k] = import_from_module(v)(config=settings, copyover=copyover_data)
            mudforge.GAME = mudforge.SERVICES["game"]

            # Start up the aiomisc entrypoint to manage our services. Very little boilerplate this way.
            with entrypoint(*mudforge.SERVICES.values(), log_format="rich") as loop:
                logging.root.addHandler(log_handler)
                logging.root.setLevel(logging.INFO)
                loop.add_signal_handler(int(signal.SIGUSR1), copyover)
                loop.run_forever()
        except Exception as err:
            logging.error(err)
            raise err

    # Remove the pidfile after process is done running.
    os.remove(pidfile)



if __name__ == "__main__":
    main()