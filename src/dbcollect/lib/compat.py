"""
compat.py - Helper functions for Python2 vs Python3 compatibility
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

# pylint: disable=unspecified-encoding,consider-using-with,unused-import,ungrouped-imports,too-few-public-methods

import sys, os, re, errno, logging, time
from pkgutil import get_data
from subprocess import Popen, PIPE

try:
    # Python 3
    from queue import Empty, Full

except ImportError:
    # Python 2
    from Queue import Empty, Full

try:
    # Python 3
    from subprocess import TimeoutExpired

except ImportError:
    # Fake exception class for Python 2
    class TimeoutExpired(Exception):
        pass

class Completed():
    """Results of running a Popen command"""
    def __init__(self, stdout, stderr, returncode):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

class Progress():
    """Show a non-moving progress message, wipe it after done"""
    def __init__(self, args):
        self.quiet = args.quiet
        self.debug = args.debug

    def __del__(self):
        if self.debug is False:
            self.message('')

    def clear(self):
        if self.debug is False:
            sys.stdout.write('\033[2K\033[G')
            sys.stdout.flush()

    def message(self, msg):
        if msg:
            logging.debug(msg)

        if self.quiet is True:
            return

        sys.stdout.write('\033[2K{0}\033[G'.format(msg))
        sys.stdout.flush()
        time.sleep(0.05)

class LinuxRelease():
    """Figure out the release major and minor version of the Linux OS - TBD"""
    def __init__(self, major, minor):
        self.major = major
        self.minor = minor

    def __repr__(self):
        return 'os release %s.%s' % (self.major, self.minor)

    @classmethod
    def parse(cls):
        try:
            # Redhat and compatible distros
            data = load_file('/etc/system-release')
            r = re.search(r'release (\d+).(\d+)', data)
            return cls(*r.groups())

        except AttributeError:
            raise ValueError('No release detected in system-release file')

        except IOError:
            pass

        try:
            # Debian and compatible distros
            data = load_file('/etc/os-release')
            r1 = re.search(r'VERSION=\"(\d+).*\"', data, re.M)
            r2 = re.search(r'VERSION=\"(\d+)\.(\d+).*\"', data, re.M)
            if r2:
                # systems with major and minor release, i.e.: VERSION="22.1 (Xia)"
                return cls(*r2.groups())
            elif r1:
                # systems with major release only, i.e. VERSION="12 (bookworm)"
                return cls(r1.group(1), None)
            else:
                return cls(None, None)

        except Exception:
            raise ValueError('No OS release detected')

def check_python_version():
    """Abort if Python has a too low version"""
    if sys.version_info[0] == 2 and sys.version_info[1] < 6:
        sys.exit("Requires Python 2.6 or higher, or 3.6 or higher")

    elif sys.version_info[0] == 3 and sys.version_info[1] < 6:
        sys.exit("Requires Python 2.6 or higher, or 3.6 or higher")

def quiet():
    """Redirect all output on stdout to /dev/null"""
    sys.stdout = open('/dev/null','w')

def load_file(path):
    """Load data from given path"""
    with open(path) as f:
        return f.read()

def write_file(path, data):
    """Write data to given path"""
    with open(path, 'w') as f:
        f.write(data)

def load_files(*args):
    """Return data in the first file found. IOError if nothing is found"""
    for path in args:
        try:
            return load_file(path)

        except IOError as e:
            if e.errno in [errno.ENOENT, errno.EACCES]:
                continue

    raise IOError(errno.ENOENT, ','.join(args))

def listdir(directory):
    """Return all files/dirs in dir, or empty list if not exists"""
    if not os.path.isdir(directory):
        return []
    return sorted(os.listdir(directory))

def popen(cmd, **kwargs):
    """Wrapper for Popen depending on Python version. On Python3, set default encoding"""
    if sys.version_info[0] == 2:
        return Popen(cmd, **kwargs)

    return Popen(cmd, encoding='utf-8', **kwargs)

def get_pkg_resource(package, resource):
    """Get a file from the zipapp package (such as an SQL script)"""
    if sys.version_info[0] == 2:
        return get_data(package, resource)

    data = get_data(package, resource)

    if data is None:
        raise ValueError('Resource not found')

    return data.decode()

def strerror(_errno):
    """Wrapper for strerror"""
    if _errno:
        return os.strerror(_errno)

    return 'Unknown Error'

def decode(buf):
    """decode binary data into text. Decoding errors are only handled on Python3"""
    if buf is None:
        return None

    if sys.version_info[0] == 2:
        return buf.decode()

    return buf.decode(errors='replace')

def execute(cmd, timeout=None, **kwargs):
    """
    Run a command, and return a Completed object.
    kwargs are added to the environment variables (i.e. if ORACLE_HOME needs to be set)
    Timeout only works on Python 3 (otherwise ignore)
    """

    command = cmd.split(' ')
    env = {}
    env.update(kwargs)

    # Setting PATH for UNIX and Linux. On AIX we also need objrepos
    env['PATH']   = '/usr/sbin:/usr/bin:/bin:/sbin:/opt/freeware/bin'
    env['ODMDIR'] = '/etc/objrepos'

    # Make ps -eo ... work on HPUX
    env['UNIX95'] = 'true'

    if sys.version_info[0] == 2:
        proc = Popen(command, env=env, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()

    else:
        proc = Popen(command, env=env, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf-8')
        stdout, stderr = proc.communicate(timeout=timeout)

    return Completed(stdout, stderr, proc.returncode)
