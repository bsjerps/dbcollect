"""
archive.py - Manage DBCollect ZIP archives
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, logging
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

from lib.compat import strerror
from lib.config import versioninfo
from lib.errors import Errors

class Archive():
    """
    A wrapper around zipfile
    Makes sure it always contains the comment which shows the magic string for dbcollect
    Files and strings are prefixed with the hostname to avoid making a mess un unzip
    """
    def __init__(self, args):
        self.prefix = os.uname()[1]
        self.path   = self.filename(args)

        logging.info('Zip file is {0}'.format(self.path))

        if os.path.exists(self.path):
            logging.info('Overwriting previous zip file')

        self.zip = ZipFile(self.path,'w', ZIP_DEFLATED, allowZip64=True)

        comment = 'dbcollect version={0} hostname={1}'.format(versioninfo['version'], self.prefix)
        self.zip.comment = comment.encode('utf-8')

    def filename(self, args):
        # return the complete path to the zip file
        if args.filename:
            if not args.filename.endswith('.zip'):
                args.filename += '.zip'
            return os.path.join('/tmp', args.filename)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return os.path.join('/tmp', 'dbcollect-{0}-{1}.zip'.format(self.prefix, timestamp))

    def __del__(self):
        if hasattr(self, 'zip'):
            self.zip.close()

    def store(self, path, tag=None, ignore=False):
        # Store an existing file in the archive. Ignore OS errors if ignore flag is set
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
                logging.error(Errors.E004, e.filename, strerror(e.errno))

        except IOError as e: # pylint: disable=duplicate-except
            if not ignore:
                logging.error(Errors.E005, e.filename, strerror(e.errno))

    def writestr(self, tag, data):
        # Store a string in the archive using tag
        try:
            self.zip.writestr(os.path.join(self.prefix, tag.lstrip('/')), data)

        except Exception as e: # pylint: disable=broad-exception-caught
            logging.warning(Errors.W003, tag, str(e))
