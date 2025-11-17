
import os, sys, logging, platform
from subprocess import Popen, PIPE

from lib.compat import Progress, decode, Full, execute, strerror
from lib.errors import Errors
from lib.config import linux_config, hpux_config, ROOTQUEUE_TIMEOUT
from lib.jsonfile import JSONPlusCommand, FileInfo

# pylint: disable=consider-using-with

def get_acct_files():
    """Find linux process accounting files (Debian and RHEL based)"""
    for topdir in ('/var/account', '/var/log/account'):
        if not os.path.isdir(topdir):
            continue
        for file in os.listdir(topdir):
            path = os.path.join(topdir, file)
            if path.endswith('.tbz2'):
                continue
            if os.path.isfile(path):
                yield path

def parse_pacct(args, path):
    """Parse a binary linux accounting file using "sa". Uncompress .gz files first"""
    jpcmd = JSONPlusCommand(args, cmd=None)
    jpcmd.name = 'cmd_root/sa-{0}.jsonp'.format(os.path.basename(path))

    fileinfo = FileInfo(path)
    jpcmd.set('fileinfo', fileinfo.dict)

    #if path.endswith('.gz'):
    if fileinfo.is_gzip:
        gunzip  = ['gunzip', '-d', '-c', path]
        sa      = ['sa', '-a', '-b', '-j', '-']
        jpcmd.set('convert', ' '.join(gunzip))
        jpcmd.set('command', ' '.join(sa))

        p1   = Popen(gunzip, stdout=PIPE, stderr=PIPE)
        proc = Popen(sa, stdin=p1.stdout, stdout=PIPE, stderr=PIPE)

        _, ge = p1.communicate()
        if p1.returncode:
            jpcmd.errors = decode(ge)

    else:
        sa   = ['sa', '-a', '-b', '-j', path]
        jpcmd.set('command', ' '.join(sa))
        proc = Popen(sa, stdout=PIPE, stderr=PIPE)

    out, err = proc.communicate()
    jpcmd.set('returncode', proc.returncode)
    if err:
        jpcmd.set('status', 'ERROR')
        jpcmd.errors = 'sa decoding error'
    else:
        jpcmd.set('status', 'OK')
        jpcmd.data = decode(out)

    return jpcmd

def get_accounting(args, rootqueue):
    """Get process accounting info on Linux"""
    system = platform.system()

    if args.no_acct:
        logging.info('Skipping process accounting (--no-acct)')
        return

    if system != 'Linux':
        logging.info('Skipping process accounting (Linux only)')
        return

    try:
        # Test if "sa" command exists
        execute('sa -V')

    except OSError as e:
        logging.warning(Errors.W005, e.filename, strerror(e.errno))

    logging.info('Collecting process accounting stats')

    progress = Progress(args)
    try:
        # Process accounting files
        for path in get_acct_files():
            msg = 'Processing accounting file %s' % path
            progress.message(msg)
            jf = parse_pacct(args, path)
            rootqueue.put(jf, timeout=ROOTQUEUE_TIMEOUT)

    except OSError as e:
        logging.warning(Errors.W005, e.filename, strerror(e.errno))

    progress.clear()

def run_root_commands(args, rootqueue):
    """Run the root commands for the OS specified in the config"""
    system = platform.system()

    if system == 'Linux':
        config = linux_config

    elif system == 'HP-UX':
        config = hpux_config

    else:
        return

    progress = Progress(args)
    for tag, cmd in config['rootcommands'].items():
        jp = JSONPlusCommand(args, cmd=cmd, progress=progress)
        jp.name = 'cmd_root/{0}.jsonp'.format(tag)
        rootqueue.put(jp, timeout=ROOTQUEUE_TIMEOUT)

    progress.clear()

def root_worker(args, exchange):
    # check if user is root and root commands are not disabled

    ready = exchange.ready.wait(10)
    if ready is False:
        logging.info('Not Ready')
        return

    if args.no_root:
        logging.info('Skipping root commands (--no-root)')
        exchange.queue.put(None, timeout=ROOTQUEUE_TIMEOUT)

    elif os.getuid() != 0:
        logging.info('Not running as root, skipping root commands')
        exchange.put(None, timeout=ROOTQUEUE_TIMEOUT)

    else:
        try:
            logging.info('Running root tasks')
            get_accounting(args, exchange.queue)
            run_root_commands(args, exchange.queue)

            exchange.queue.put(None, timeout=ROOTQUEUE_TIMEOUT)

        except Full:
            logging.error(Errors.E045)
            sys.exit(10)

        except Exception as e: # pylint: disable=broad-exception-caught
            logging.exception(Errors.E001, e)
            sys.exit(99)
