"""
compat.py - Helper functions for Python2 vs Python3 compatibility
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

# pylint: disable=unspecified-encoding, consider-using-with

import sys
from pkgutil import get_data
from subprocess import Popen

def check_python_version():
    if sys.version_info[0] == 2 and sys.version_info[1] < 6:
        sys.exit("Requires Python 2.6 or higher, or 3.6 or higher")

    elif sys.version_info[0] == 3 and sys.version_info[1] < 6:
        sys.exit("Requires Python 2.6 or higher, or 3.6 or higher")

def quiet():
    sys.stdout = open('/dev/null','w')

def load_file(path):
    with open(path) as f:
        return f.read()

def write_file(path, data):
    with open(path, 'w') as f:
        f.write(data)

def popen(cmd, **kwargs):
    if sys.version_info[0] == 2:
        return Popen(cmd, **kwargs)

    return Popen(cmd, **kwargs, encoding='utf-8')

def get_pkg_resource(package, resource):
    if sys.version_info[0] == 2:
        return get_data(package, resource)

    data = get_data(package, resource)

    if data is None:
        raise ValueError('Resource not found')

    return data.decode()
