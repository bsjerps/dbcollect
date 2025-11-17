"""
jsonfile.py - Data file formatting for dbcollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import sys, os, platform, logging, json, time, pwd
from datetime import datetime

try:
    from lib.buildinfo import buildinfo

except ImportError:
    print("Error: No buildinfo")
    sys.exit(20)

from lib.errors import Errors
from lib.user import username, usergroup, usergroups, getuser, getgroup
from lib.config import versioninfo
from lib.compat import load_file, write_file, strerror, execute, TimeoutExpired

def get_timestamp(ts):
    """Workaround for strftime() not working (HP-UX)"""
    return '{0:04}-{1:02}-{2:02} {3:02}:{4:02}'.format(ts.year, ts.month, ts.day, ts.hour, ts.minute)

class FileInfo():
    def __init__(self, path):
        self.path = path
        self.info = {}
        self.info['path']   = self.path
        self.info['status'] = None
        self._data = None

    def get_info(self):
        if not os.path.isfile(self.path):
            self.info['status'] = 'Nonexistent'
            return

        try:
            statinfo = os.stat(self.path)
            self.info['dirname'] = os.path.dirname(self.path)
            self.info['basename'] = os.path.basename(self.path)
            self.info['size']  = statinfo.st_size
            self.info['mode']  = oct(statinfo.st_mode)
            self.info['uid']   = statinfo.st_uid
            self.info['gid']   = statinfo.st_gid
            self.info['user']  = getuser(statinfo.st_uid)
            self.info['group'] = getgroup(statinfo.st_gid)
            self.info['hardlinks'] = statinfo.st_nlink
            self.info['atime'] = datetime.fromtimestamp(int(statinfo.st_atime)).strftime("%Y-%m-%d %H:%M")
            self.info['mtime'] = datetime.fromtimestamp(int(statinfo.st_mtime)).strftime("%Y-%m-%d %H:%M")

        except IOError as e:
            self.info['status'] = 'ERROR'
            self.info['error']  = strerror(e.errno)

    @property
    def data(self):
        if self._data is None:
            self._data = load_file(self.path)
        return self._data

    @property
    def is_gzip(self):
        magic = b'\x1f\x8b'
        with open(self.path, 'rb') as f:
            buf = f.read(2)

        return buf == magic

    @property
    def dict(self):
        self.get_info()
        return self.info

class JSONPlus():
    """
    Container for a JSONPlus file
    JSONPlus file format is simply a JSON with the data of a command or file appended
    """
    def __init__(self):
        self.info = {}
        self.info['application']  = 'dbcollect'
        self.info['version']      = versioninfo['version']
        self.info['hostname']     = platform.uname()[1]  # Hostname
        self.info['machine']      = platform.machine()   # x86_64 | sun4v | 00F6035A4C00 (AIX) | AMD64 etc...
        self.info['system']       = platform.system()    # Linux  | SunOS | SunOS | AIX | Windows
        self.info['processor']    = platform.processor() # x86_64 | i386 | sparc | powerpc | Intel64 Family ...
        self.info['timestamp']    = get_timestamp(datetime.now())
        self.info['timestamputc'] = get_timestamp(datetime.utcnow())
        self.info['status']       = None
        self.name   = None
        self.errors = None
        self.data   = ''

    def set(self, name, val):
        """Setter for any kind of metric"""
        self.info[name] = val

    def dump(self):
        """Return the data as JSON text"""
        return json.dumps(self.info, indent=2)

    def save(self, path):
        """Save self as jsonp file"""
        write_file(path, self.jsonp())

    def jsonp(self):
        """Return the data as JSONPlus"""
        if self.errors:
            self.info['errors'] = self.errors.splitlines()
        data = json.dumps(self.info, indent=2)
        if self.data:
            data += '\n'
            data += self.data
        return data

class JSONPlusMeta(JSONPlus):
    """Container for meta.json"""
    def __init__(self):
        JSONPlus.__init__(self)  # Avoid super() as it differs on Python 2
        runinfo = {}
        runinfo['python']      = platform.python_version()
        runinfo['timezone']    = time.strftime("%Z", time.gmtime()) # The system's configured timezone
        runinfo['cmdline']     = ' '.join(sys.argv)                 # Command by which we are called
        runinfo['username']    = username()                         # Username (after switching from root)
        runinfo['usergroup']   = usergroup()                        # Primary group
        runinfo['usergroups']  = ','.join(usergroups())             # List of groups we are a member of
        runinfo['zipname']     = os.path.realpath(__loader__.archive)
        self.info['runinfo']   = runinfo
        self.info['buildinfo'] = buildinfo

class JSONPlusCommand(JSONPlus):
    def __init__(self, args, cmd, progress=None, **kwargs):
        JSONPlus.__init__(self)
        user = pwd.getpwuid(os.getuid()).pw_name
        self.info['mediatype']  = 'command'
        self.info['format']     = 'text'
        self.info['command']    = cmd
        self.info['user']       = user
        self.info['returncode'] = None

        """
        Execute a command and return the output with the header.
        Forward kwargs to the execute function (extra env variables)
        Also record status and errors
        """

        if cmd is None:
            return

        basecmd = cmd.split()[0]
        if args.skip_cmd and basecmd in args.skip_cmd.split(','):
            self.info['status'] = 'SKIPPED'
            logging.debug('Skipping command %s', cmd)
            return

        try:
            msg = 'running command (%s): %s' % (user, cmd)

            if progress:
                progress.message(msg)

            completed = execute(cmd, timeout=10, **kwargs)
            self.data   = completed.stdout
            self.errors = completed.stderr
            self.info['returncode'] = completed.returncode

            if completed.returncode:
                self.info['status'] = 'FAILED'
            else:
                self.info['status'] = 'OK'

        except TimeoutExpired as e:
            logging.debug('Timeout on %s', cmd)
            self.info['status']     = 'TIMEOUT'
            self.info['returncode'] = None
            self.errors = str(e)

        except OSError as e:
            self.info['status']     = 'ERROR'
            self.errors             = strerror(e.errno)
            self.info['returncode'] = None

class JSONPlusFile(JSONPlus):
    def __init__(self, path, progress=None):
        JSONPlus.__init__(self)
        self.info['mediatype'] = 'flatfile'
        self.info['format']    = 'raw'
        self.info['path']      = path

        if not os.path.isfile(path):
            logging.debug('%s: No such file or directory', path)
            self.info['status'] = 'Nonexistent'
            return

        try:
            msg = 'reading file: %s' % path
            if progress:
                progress.message(msg)

            fileinfo  = FileInfo(path)
            self.data = fileinfo.data
            fileinfo.info['status'] = 'OK'
            self.info['fileinfo'] = fileinfo.dict

        except IOError as e:
            self.info['status'] = 'ERROR'
            self.errors = strerror(e.errno)

        except Exception as e: # pylint: disable=broad-exception-caught
            self.info['status'] = 'ERROR'
            self.info['status'] = 'Critical Error'
            logging.critical(Errors.E015, path, e)

class JSONPlusDBInfo(JSONPlus):
    """Create a dbinfo report"""
    def __init__(self, instance, path, **kwargs):
        JSONPlus.__init__(self)
        self.info['mediatype'] = 'dbinfo'
        self.info['format']    = 'sqlplus'
        self.info['oracle']    = instance.meta
        self.info['sqlplus']   = kwargs

        try:
            self.data = load_file(path)
            self.info['status'] = 'OK'
            os.unlink(path)

        except Exception: # pylint: disable=broad-exception-caught
            self.info['status'] = 'ERROR'
            self.errors = 'Data not available'

class JSONPlusDirectories(JSONPlus):
    """Report contents of given directories"""
    def __init__(self, *dirs):
        JSONPlus.__init__(self)
        self.info['directories'] = []
        for directory in dirs:
            if not os.path.isdir(directory):
                self.info['directories'].append({ 'directory': directory, 'exists': False })
                continue
            files = []
            for file in sorted(os.listdir(directory)):
                path = os.path.join(directory, file)
                if not os.path.isfile(path):
                    continue
                st = os.stat(path)
                files.append({
                    'path': path,
                    'size': st.st_size,
                    'mtime': datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    'user': getuser(st.st_uid),
                    'group': getgroup(st.st_gid)
                })
            self.info['directories'].append({ 'directory': directory, 'files': files})
