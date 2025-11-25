"""
user.py - Manage DBCollect ZIP archives
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
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

import os, sys, re
import pwd, grp

from lib.errors import CustomException
from lib.compat import get_pkg_resource, execute

def _get_user(args):
    """Get the user to run as"""

    # If a user was given, use it
    if args.user:
        return args.user

    # Find the first user that runs oracle pmon
    psout = execute('ps -eo user,args')
    r = re.search(r'(\S+)\s+ora_pmon_(\S+)', psout.stdout)
    if r:
        return r.group(1)

    # If nothing found, use nobody
    return 'nobody'

def get_user(args):
    """Get the username to run dbcollect with"""

    # Get required username 
    user = _get_user(args)

    # Check if the user exists
    try:
        pwd.getpwnam(user)
        return user

    except KeyError:
        raise CustomException("No such user: %s" % user)

def check_zipapp():
    """Checks access to the dbcollect zipapp package"""
    # Try to read a file from the package
    try:
        get_pkg_resource('lib', 'config.py')

    except (OSError,IOError):
        ziploc = os.path.realpath(sys.path[0])
        raise CustomException('Cannot read dbcollect package %s, exiting...' % ziploc)

def drop_user(user):
    """Drops user privileges from root to the given user"""
    if os.getuid() != 0:
        return

    # Get user/group info
    try:
        uid    = pwd.getpwnam(user).pw_uid
        gid    = pwd.getpwnam(user).pw_gid
        groups = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]

    except KeyError:
        raise CustomException("User %s not available" % user)

    if uid == 0:
        raise CustomException('Root not allowed')

    # drop privileges
    os.setgid(gid)
    groups.append(gid)
    os.setgroups(groups)
    os.setuid(uid)

    # Set file creation mask
    os.umask(0o0022)

    check_zipapp()

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
