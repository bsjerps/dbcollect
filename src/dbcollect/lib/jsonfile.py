"""
jsonfile.py - Data file formatting for dbcollect
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import sys, os, platform, logging, json, time
from datetime import datetime

try:
    from lib.buildinfo import buildinfo
except ImportError:
    print("Error: No buildinfo")
    sys.exit(20)

from lib.errors import Errors
from lib.user import username, usergroup, usergroups, getuser, getgroup
from lib.config import versioninfo
from lib.functions import execute

def get_timestamp(ts):
    """Workaround for strftime() not working (HP-UX)"""
    return '{0:04}-{1:02}-{2:02} {3:02}:{4:02}'.format(ts.year, ts.month, ts.day, ts.hour, ts.minute)

class JSONFile():
    """
    Container for a JSONPlus file
    JSONPlus file format is simply a JSON with the data of a command or file appended
    """
    def __init__(self, cmd=None, path=None, sudo=False, **kwargs):
        self.info = {}
        self.info['application']  = 'dbcollect'
        self.info['version']      = versioninfo['version']
        self.info['hostname']     = platform.uname()[1]  # Hostname
        self.info['machine']      = platform.machine()   # x86_64 | sun4v | 00F6035A4C00 (AIX) | AMD64 etc...
        self.info['system']       = platform.system()    # Linux  | SunOS | SunOS | AIX | Windows
        self.info['processor']    = platform.processor() # x86_64 | i386 | sparc | powerpc | Intel64 Family ...
        self.info['timestamp']    = get_timestamp(datetime.now())
        self.info['timestamputc'] = get_timestamp(datetime.utcnow())
        self.info.update(kwargs)
        self.errors = ''
        self.data   = ''
        if cmd:
            self.execute(cmd, sudo)
        elif path:
            self.readfile(path)
        self.info.update(kwargs)

    def meta(self):
        """Set default metadata fields"""
        runinfo = {}
        runinfo['python']      = platform.python_version()
        runinfo['timezone']    = time.strftime("%Z", time.gmtime())           # The system's configured timezone
        runinfo['cmdline']     = ' '.join(sys.argv)        # Command by which we are called
        runinfo['username']    = username()                # Username (after switching from root)
        runinfo['usergroup']   = usergroup()               # Primary group
        runinfo['usergroups']  = ','.join(usergroups())    # List of groups we are a member of
        runinfo['zipname']     = os.path.realpath(__loader__.archive)
        self.info['runinfo']   = runinfo
        self.info['buildinfo'] = buildinfo

    def set(self, name, val):
        """Setter for any kind of metric"""
        self.info[name] = val

    def execute(self, cmd, sudo=False, **kwargs):
        """
        Execute a command and return the output with the header.
        Forward kwargs to the execute function (extra env variables)
        Also record status and errors
        """
        self.info['mediatype'] = 'command'
        self.info['format']    = 'text'
        self.info['command']   = cmd
        out, err = None, None
        if sudo is True:
            basecmd = cmd.split()[0]

            if not os.path.exists('/usr/bin/sudo'):
                self.info['status'] = 'ERROR'
                self.errors         = '/usr/bin/sudo not found'
                return
            cmd = 'sudo -n {0}'.format(cmd)
            self.info['sudo'] = True
            self.info['fullcommand'] = cmd

            which_out, which_err, which_rc = execute('which {0}'.format(basecmd))
            if which_rc==1:
                self.errors = which_err
                self.info['status']     = 'SUDO_NONEXISTENT'
                self.info['returncode'] = which_rc
                return
        try:
            logging.debug('running command: %s', cmd)
            out, err, rc = execute(cmd, **kwargs)
            self.data   = out
            self.errors = err
            if rc==1 and err.startswith('sudo'):
                self.info['status']     = 'SUDO_FAIL'
            else:
                self.info['status']     = 'OK'
            self.info['returncode'] = rc
        except OSError as e:
            self.info['status']     = 'ERROR'
            self.errors             = os.strerror(e.errno)
            self.info['returncode'] = None

    def readfile(self, path):
        """
        Retrieve a flat file and return the output with the header.
        Also record status and errors
        """
        self.info['mediatype'] = 'flatfile'
        self.info['format']    = 'raw'
        self.info['path']      = path
        if not os.path.isfile(path):
            logging.debug('%s: No such file or directory', path)
            self.info['status'] = 'Nonexistent'
            return
        try:
            statinfo = os.stat(path)
            self.info['size']  = statinfo.st_size
            self.info['mode']  = oct(statinfo.st_mode)
            self.info['user']  = getuser(statinfo.st_uid)
            self.info['group'] = getgroup(statinfo.st_gid)
            self.info['atime'] = datetime.fromtimestamp(int(statinfo.st_atime)).strftime("%Y-%m-%d %H:%M")
            self.info['mtime'] = datetime.fromtimestamp(int(statinfo.st_mtime)).strftime("%Y-%m-%d %H:%M")
            with open(path) as f:
                self.data = f.read()
            self.info['status'] = 'OK'

        except IOError as e:
            self.info['status'] = 'ERROR'
            self.errors = os.strerror(e.errno)

        except Exception as e:
            self.info['status'] = 'ERROR'
            self.info['status'] = 'Critical Error'
            logging.critical(Errors.E015, path, e)

    def dbinfo(self, instance, name, path):
        """
        Create a dbinfo report
        """
        self.info['mediatype'] = 'dbinfo'
        self.info['format']    = 'sqlplus'
        self.info['script']    = name
        self.info['oracle']    = instance.meta
        try:
            with open(path) as f:
                self.data = f.read()
            os.unlink(path)

        except Exception:
            self.info['status'] = 'ERROR'
            self.errors = 'Data not available'

    def dir(self, *dirs):
        """Report contents of given directories"""
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

    def dump(self):
        """Return the data as JSON text"""
        return json.dumps(self.info, indent=2)

    def save(self, path):
        """Save self as jsonp file"""
        with open(path, 'w') as f:
            f.write(self.jsonp())

    def jsonp(self):
        """Return the data as JSONPlus"""
        if self.errors:
            self.info['errors'] = self.errors.splitlines()
        data = json.dumps(self.info, indent=2)
        if self.data:
            data += '\n'
            data += self.data
        return data
