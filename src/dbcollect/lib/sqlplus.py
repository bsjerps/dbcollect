"""
sqlplus.py - Run SQL*Plus and other binaries in ORACLE_HOME
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, logging
from subprocess import PIPE, STDOUT
from lib.errors import Errors, SQLPlusError
from lib.compat import popen, strerror

def sqlplus(orahome, sid, connectstring, tmpdir, quiet=False, timeout=None):
    """
    Create a Popen() SQL*Plus session
    if quiet=True, redirect stdout to /dev/null.
    Note: SQL*Plus never writes to stderr.
    """
    env = {}
    env['PATH'] = '/usr/sbin:/usr/bin:/bin:/sbin:/opt/freeware/bin'
    env['ORACLE_HOME'] = orahome
    env['ORACLE_SID'] = sid

    sqlplus_bin = os.path.join(orahome, 'bin/sqlplus')

    if connectstring:
        cmd  = [sqlplus_bin, '-S', '-L', connectstring]
        msg  = '%s: executing "%s"' % (sid, ' '.join(cmd[:-1]) + ' <connectstring>')
    else:
        cmd  = [sqlplus_bin, '-S', '-L', '/', 'as', 'sysdba']
        msg  = '%s: executing "%s"' % (sid, ' '.join(cmd))

    if timeout is not None:
        if os.path.exists('/usr/bin/timeout'):
            cmd.insert(0, str(timeout))
            cmd.insert(0, 'timeout')
        else:
            logging.debug('Timeout not detected')

    if quiet:
        stdout = open('/dev/null', 'wb')
    else:
        stdout = PIPE

    try:
        logging.debug(msg)
        proc = popen(cmd, cwd=tmpdir, bufsize=0, env=env, stdin=PIPE, stdout=stdout, stderr=STDOUT)
        return proc

    except OSError as e:
        raise SQLPlusError(Errors.E019, sid, strerror(e.errno))
