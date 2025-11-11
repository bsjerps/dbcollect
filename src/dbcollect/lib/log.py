"""
log.py - Manage DBCollect logging
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+

logsetup sets up dual logging via separate handlers, one is the dbcollect logfile
which logs at DEBUG level (most everything)
the other is the consolehandler which logs at INFO or ERROR if --quiet is requested.
The filter prevents traceback logs on the console but these are still logged
to the logfile for diagnostic purposes.

logsetup must be called AFTER switching users, or strange things will happen.
"""

import sys, logging
from lib.errors import Errors

class TracebackInfoFilter(logging.Filter):
    """Clear or restore the exception on log records"""

    def __init__(self, clear=True):
        self.clear = clear
        super().__init__()

    def filter(self, record):
        if self.clear:
            record._exc_info_hidden, record.exc_info = record.exc_info, None
            # clear the exception traceback text cache, if created.
            record.exc_text = None
        elif hasattr(record, "_exc_info_hidden"):
            record.exc_info = record._exc_info_hidden
            del record._exc_info_hidden
        return True

def logsetup(args):
    """Setup logging both to logpath and stderr"""

    logpath = "/tmp/dbcollect.log"

    try:
        logging.basicConfig(filename=logpath,
            filemode = 'w',
            level    = logging.DEBUG,
            format   = "%(asctime)s:%(levelname)-8s: %(message)s",
            datefmt  = '%Y-%m-%d %I:%M:%S')

        handler = logging.StreamHandler()
        handler.addFilter(TracebackInfoFilter())
        handler.setFormatter(logging.Formatter('%(levelname)-8s : %(message)s', datefmt='%Y-%m-%d-%H:%M:%S'))

        if args.debug:
            handler.setLevel(logging.DEBUG)
        elif args.quiet:
            handler.setLevel(logging.ERROR)
        else:
            handler.setLevel(logging.INFO)

        logging.getLogger().addHandler(handler)

    except Exception as e:
        logging.fatal(Errors.E014, logpath, e)
        raise

def exception_handler(func):
    """Decorator to catch CTRL-C and other exceptions (multiprocessing)
    This prevents a mess of error messages from different processes
    """
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            logging.warning(Errors.W001, func.__name__)
            sys.exit(1)
        except Exception as e:
            logging.exception(Errors.E013, func.__name__, e)
            sys.exit(99)
    return inner
