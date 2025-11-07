"""
functions.py - Some functions for DBCollect
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, sys, errno
from subprocess import Popen, PIPE
from pkgutil import get_data

def listdir(directory):
    """Return all files/dirs in dir, or empty list if not exists"""
    if not os.path.isdir(directory):
        return []
    return sorted(os.listdir(directory))

def getscript(name):
    """Directly get an SQL script from the Python package"""
    try:
        if sys.version_info[0] == 2:
            return get_data('sql', name)
        return get_data('sql', name).decode()
    except OSError:
        raise RuntimeError("Cannot load script {0}".format(name))

def getfile(*args):
    """try each file from paths until readable, try next if not exists or no access"""
    for path in args:
        try:
            with open(path) as f:
                return f.read()
        except IOError as e:
            if e.errno in [errno.ENOENT, errno.EACCES]:
                continue
            raise

def execute(cmd, **kwargs):
    """
    Run a command, and return the output of stdout. Any stderr messages will be logged.
    If the command fails (i.e. does not exists or exits with non-zero return code), logs an error
    Even if the command fails, still an empty string is returned so the program continues.
    kwargs are added to the environment variables (i.e. if ORACLE_HOME needs to be set)
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
    else:
        proc = Popen(command, env=env, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf-8')
    stdout, stderr = proc.communicate()
    return (stdout, stderr, proc.returncode)

def sudosetup():
    sudopath = '/etc/sudoers.d/dbcollect'
    print('Installing sudoers file: {0}'.format(sudopath))
    sudoers = get_data('lib', 'sudoers').decode()
    try:
        with open(sudopath, 'w') as f:
            f.write(sudoers)
            os.chmod(sudopath, 0o600)
    except OSError as e:
        if e.errno == 13:
            print('Cannot install sudoers, manually copy it to {0}'.format(sudopath))
            print()
            print(sudoers)
        else:
            print(e)
