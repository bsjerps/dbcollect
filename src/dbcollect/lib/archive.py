"""
archive.py - Manage DBCollect ZIP archives
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, logging
from zipfile import ZipFile, ZIP_DEFLATED

from lib.config import versioninfo
from lib.errors import Errors, ZipCreateError

class Archive():
    """
    A wrapper around zipfile
    Makes sure it always contains the comment which shows the magic string for dbcollect
    Files and strings are prefixed with the hostname to avoid making a mess un unzip
    """
    zip = None
    def __init__(self, path, overwrite=False):
        self.ok      = False
        self.prefix  = os.uname()[1]
        self.path    = path
        if os.path.exists(self.path) and not overwrite:
            raise ZipCreateError(Errors.E020, path)
        try:
            self.zip = ZipFile(self.path,'w', ZIP_DEFLATED, allowZip64=True)

        except OSError:
            raise ZipCreateError(Errors.E003, path)

        comment = 'dbcollect version={0} hostname={1}'.format(versioninfo['version'], self.prefix)
        self.zip.comment = comment.encode('utf-8')

    def __del__(self):
        if self.zip:
            self.zip.close()
        if self.ok is False:
            os.rename(self.path, self.path.replace('.zip','.failed.zip'))

    def store(self, path, tag=None, ignore=False):
        if tag:
            fulltag = os.path.join(self.prefix, tag)
        else:
            fulltag = os.path.join(self.prefix, path.lstrip('/'))
        if not os.path.isfile(path):
            logging.debug("Skipping %s (nonexisting)", path)
            return
        try:
            self.zip.write(path, fulltag)
        except OSError as e:
            if not ignore:
                logging.error(Errors.E004, e.filename, os.strerror(e.errno))
        except IOError as e:
            if not ignore:
                logging.error(Errors.E005, e.filename, os.strerror(e.errno))

    def writestr(self, tag, data):
        try:
            self.zip.writestr(os.path.join(self.prefix, tag.lstrip('/')), data)
        except Exception as e:
            logging.warning(Errors.W003, tag, str(e))
