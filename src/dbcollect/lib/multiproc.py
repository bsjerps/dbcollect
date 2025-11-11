"""
multiproc.py - Multiprocessing classes for DBCollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, tempfile
from shutil import rmtree
from multiprocessing import Event, Queue

class Tempdir():
    """Temp directory class with subdirs, which cleans up the tempdir when it gets deleted"""
    def __init__(self, args):
        self.tempdir = tempfile.mkdtemp(prefix = os.path.join(args.tempdir, 'dbcollect_'))
        for subdir in ('lock','dbinfo','awr','log'):
            os.mkdir(os.path.join(self.tempdir, subdir))

    def __del__(self):
        rmtree(self.tempdir)

class Shared():
    """Container class for messages and sharing data between processes"""
    def __init__(self, args, instance, tempdir):
        self.args      = args
        self.instance  = instance
        self.tempdir   = tempdir
        self.jobs      = Queue(60)
        self.done      = Event()
