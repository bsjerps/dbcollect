"""
sqlplus.py - Run SQL*Plus and other binaries in ORACLE_HOME
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, sys, logging
from subprocess import Popen, PIPE, STDOUT
from lib.errors import Errors, SQLPlusError

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
    else:
        cmd  = [sqlplus_bin, '-S', '-L', '/', 'as', 'sysdba']

    if timeout is not None:
        if os.path.exists('/usr/bin/timeout'):
            cmd.insert(0, str(timeout))
            cmd.insert(0, 'timeout')
        else:
            logging.debug('Timeout not detected')

    if quiet:
        stdout = open('/dev/null', 'w')
    else:
        stdout = PIPE

    try:
        logging.debug('%s: executing "%s"', sid, ' '.join(cmd))
        if sys.version_info[0] == 2:
            proc = Popen(cmd, cwd=tmpdir, bufsize=0, env=env, stdin=PIPE, stdout=stdout, stderr=STDOUT)
        else:
            proc = Popen(cmd, cwd=tmpdir, bufsize=0, env=env, stdin=PIPE, stdout=stdout, stderr=STDOUT, encoding='utf-8')

        return proc

    except OSError as e:
        raise SQLPlusError(Errors.E019, sid, os.strerror(e.errno))
