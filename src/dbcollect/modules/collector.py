"""
worker.py - run the core dbcollect stuff in a separate process with non-root privileges
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, sys, logging, platform, time
from multiprocessing import Process, Queue, Event

from lib.compat import load_file, quiet, strerror, Empty
from lib.config import WORKQUEUE_TIMEOUT, DBCOLLECT_LOG, versioninfo
from lib.log import logfile_handler
from lib.errors import CustomException, Errors, DBCollectFailed, DBWorkerFailed
from lib.user import drop_user, username, get_user
from lib.jsonfile import JSONPlusMeta
from lib.archive import Archive

from modules.rootworker import root_worker
from modules.oracle import oracle_info
from modules.syscollect import host_info

class Exchange():
    """Container class for sharing between multiple processes"""
    def __init__(self):
        self.ready = Event()
        self.queue = Queue(5)

    def drain(self):
        # Empties the queue to prevent hanging on join()
        while self.queue.empty() is False:
            self.queue.get()

def collect_wrapper(args):
    """
    Sets up the environment, then runs a root and a non-root worker.

    The root worker sends the collected info over a queue to be stored in the
    ZIP file owned by the non-root worker.

    If dbcollect was not started as root, the root_worker will not send any data
    """
    try:
        # create multiprocessing container
        exchange = Exchange()

        # Get user to run worker with
        user = get_user(args)

        # Setup logging
        try:
            logfile_handler(args, user, DBCOLLECT_LOG)
            logging.info('dbcollect {0} - database and system info collector'.format(versioninfo['version']))
            logging.info('For diagnosing errors, use --error option. More info on https://wiki.dirty-cache.com/DBCollect/Troubleshooting')
            logging.info('Python version {0}'.format(platform.python_version()))

        except IOError as e:
            logging.critical(Errors.E007, DBCOLLECT_LOG, strerror(e.errno))
            return

        # run dbcollect workers
        proc_root = Process(target=root_worker, args=(args, exchange))
        proc_dbc  = Process(target=dbcollect_worker, name='DBCollect_worker', args=(args, exchange, user))

        proc_dbc.start()
        proc_root.start()
        time.sleep(1)
        proc_dbc.join()

        # Drain the queue if there are items left from the consumer, to prevent hang
        exchange.drain()

        proc_root.join(timeout=10)
        if proc_root.exitcode is None:
            logging.debug('Root worker exitcode %s', proc_root.exitcode)

        # Drain the queue if there are items left from the producer, to prevent hang
        exchange.drain()

        if proc_dbc.exitcode:
            raise DBWorkerFailed('%s' % proc_dbc.exitcode)

    except KeyboardInterrupt:
        logging.fatal(Errors.E002)

def get_root_tasks(archive, exchange):
    """
    Pick up the task data from the root queue
    Note that this function runs as non-root user
    """
    # Signal the root worker to start sending
    exchange.ready.set()

    # Pick up task data until root worker is done
    while True:
        try:
            # Timeout must be larger than the root_worker timeout
            obj = exchange.queue.get(timeout=WORKQUEUE_TIMEOUT)

            # Keep processing until the root_worker sends None to signal completion
            if obj is None:
                break

            archive.writestr(obj.name, obj.jsonp())

        except Empty:
            # Break on timeout (usually caused by long-running root tasks or errors in root worker)
            logging.error(Errors.E046)
            break

def dbcollect_worker(args, exchange, user):
    """Runs most of the work as non-root user"""
    try:
        # Drop root privileges first
        drop_user(user)

        logging.info('Current user is {0}'.format(username()))
        logging.info('Command line is {0}'.format(' '.join(sys.argv)))
        try:
            osname = load_file('/etc/system-releasee')
        except IOError:
            osname = 'Unknown'
        logging.info('OS version is {0}'.format(osname.strip()))

        # Open ZIP archive (as non-root user)
        try:
            archive = Archive(args)

        except (OSError, IOError) as e:
            logging.critical(Errors.E003, e.filename)
            sys.exit(10)

        try:
            if args.quiet:
                quiet()

            metainfo = JSONPlusMeta()
            archive.writestr('meta.json', metainfo.dump())

            # Get the data from the root worker early to prevent timeouts
            get_root_tasks(archive, exchange)

            if not args.no_sys:
                host_info(archive, args)

            if not args.no_ora:
                oracle_info(archive, args)

            # If there was no exception, ZIP file was created successfully
            logging.info('Zip file {0} is created succesfully.'.format(archive.path))
            logging.info('Do not modify the {0} zipfile before transferring'.format(archive.path))
            logging.info('Upload the unmodified file to https://cloud.sjerps.eu/s/dbcollect or send via an alternative method')
            logging.info("Finished")

        except (OSError, IOError) as e:
            logging.error(Errors.E012, e.filename, strerror(e.errno))
            raise DBCollectFailed

        except CustomException as e:
            logging.exception(e)
            raise DBCollectFailed

        except Exception as e:
            logging.exception(Errors.E001, e)
            raise DBCollectFailed

    except KeyboardInterrupt:
        logging.error(Errors.E002)

        logging.critical('Failed')
        sys.exit(98)

    except DBCollectFailed as e:
        # Handle known errors that caused fail
        logging.critical('DBCollect ZIP file did not finish completely, please try again')
        logging.critical('Failed')
        sys.exit(10)

    except Exception as e: # pylint: disable=broad-exception-caught
        # Handle anything else (caused by bug)
        logging.critical(Errors.E001, str(e))
        logging.exception(e)
        logging.critical('Failed')
        sys.exit(99)

    finally:
        # store logfile in the archive and clean up
        try:
            data = load_file(DBCOLLECT_LOG)
            archive.writestr('dbcollect.log', data)
            os.unlink(DBCOLLECT_LOG)
            if args.debug:
                print('')
                print('Contents of the dbcollect logfile:')
                print(data)

        except IOError as e:
            logging.error(Errors.E012, DBCOLLECT_LOG, strerror(e.errno))

        except UnboundLocalError:
            # Just to prevent linter errors
            pass
