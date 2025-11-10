"""
user.py - Manage DBCollect ZIP archives
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+

Switch user if the current user is root
This serves 2 purposes:
1) Safety against bugs
2) Oracle SQL*Plus must be executed as a 'sysdba' which requires an OS user
   with these permissions. Usually 'oracle'.

The primary group and other group memberships are also detected and setup.

If 'oracle' is not found, switch to 'nobody' so dbcollect will still work
safely on systems without Oracle.
"""

import os, sys, re, logging
import pwd, grp
from multiprocessing import Process
from subprocess import PIPE, CalledProcessError, check_call

from lib.errors import CustomException, Errors
from lib.compat import write_file, get_pkg_resource
from lib.functions import execute
from lib.log import logsetup

def dbuser():
    """"Find the first Oracle database owner"""
    stdout, _, _ = execute('ps -eo uid,args')
    for uid, cmd in re.findall(r'(\d+)\s+(.*)', stdout):
        r = re.match(r'ora_pmon_(\w+)', cmd)
        if r:
            user = pwd.getpwuid(int(uid)).pw_name
            return user
    return None

def sudowrapper(args, func):
    """Run collection as non-root, create temporary sudoers file"""
    os.umask(0o0022)
    sudoers_path = '/etc/sudoers.d/dbcollect'
    log_path = '/tmp/dbcollect.log'

    if args.user:
        user = args.user
    else:
        user = dbuser()

    sudoers = get_pkg_resource('lib', 'sudoers')
    sudoers += '{0}	ALL = (ALL) NOPASSWD: DBCOLLECT\n'.format(user)

    try:
        if os.getuid() == 0 and not args.no_sudo:
            try:
                write_file(sudoers_path, sudoers)
            except OSError:
                print('Writing sudoers failed')

        logsetup(args)

        proc = Process(target=switchuser, name='UserSub', args=(args, user, func))
        proc.start()
        proc.join()

    except KeyboardInterrupt:
        logging.fatal(Errors.E002)

    finally:
        if os.path.exists(log_path):
            os.unlink(log_path)

        if os.path.exists(sudoers_path):
            os.unlink(sudoers_path)

def switchuser(args, user, func):
    """Call func as a different user with the same parameters"""
    if os.getuid() != 0:
        func(args)
        return

    if user is None:
        user = 'oracle'
    try:
        uid = pwd.getpwnam(user).pw_uid
        home = pwd.getpwnam(user).pw_dir
    except KeyError:
        logging.warning("User {0} not available, trying 'nobody'".format(user))
        try:
            user = 'nobody'
            uid = pwd.getpwnam(user).pw_uid
            home = '/tmp'
        except KeyError:
            print("User nobody not available, giving up")
            sys.exit(20)

    gid = pwd.getpwnam(user).pw_gid
    os.setgid(gid)
    groups = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]
    groups.append(gid)
    os.setgroups(groups)
    os.setuid(uid)

    try:
        get_pkg_resource('lib', 'config.py')
    except PermissionError:
        ziploc = os.path.realpath(sys.path[0])
        print('Cannot read dbcollect package {0}, exiting...'.format(ziploc))
        sys.exit(10)

    try:
        os.chdir(home)
    except OSError:
        os.chdir('/tmp')

    try:
        if not args.no_sudo:
            check_call(['sudo', '-n', '-l'], stdout=PIPE, stderr=PIPE)

    except CalledProcessError:
        raise CustomException('sudo failed for user {0}'.format(user))

    func(args)

def username():
    """Return the username for the current userid"""
    return pwd.getpwuid(os.getuid()).pw_name

def usergroup():
    """Return the primary group for the current groupid"""
    return grp.getgrgid(os.getgid()).gr_name

def usergroups():
    """Return the groups for the current user"""
    user = pwd.getpwuid(os.getuid()).pw_name
    return [g.gr_name for g in grp.getgrall() if user in g.gr_mem]

def getuser(uid):
    """Return the username for a given uid"""
    uinfo = pwd.getpwuid(uid)
    return uinfo.pw_name

def getgroup(gid):
    """Return the groupname for a given gid"""
    ginfo = grp.getgrgid(gid)
    return ginfo.gr_name
