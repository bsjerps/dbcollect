"""
updater.py - OS and system functions for dbcollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""
try:
    from urllib2 import urlopen, Request, HTTPError, URLError
except ImportError:
    from urllib.request import Request, urlopen

import os, sys, json, logging
from shutil import move

def retrieve(url):
    """Retrieve the raw data from a url"""
    try:
        request  = Request(url)
        response = urlopen(request)
        return response.read()
    except (HTTPError, URLError) as e:
        logging.error("%s", e)
        sys.exit(10)

def update(current):
    _tmpfile = '/tmp/dbcollect'
    _apiurl  = 'https://api.github.com/repos/bsjerps/dbcollect/releases/latest'
    _target  = '/usr/local/bin/dbcollect'

    logging.basicConfig(level=logging.DEBUG,format='%(levelname)-8s : %(message)s')
    logging.info('Retrieving GitHub metadata from %s', _apiurl)
    info        = json.loads(retrieve(_apiurl))
    version     = info['tag_name'].lstrip('v')
    downloadurl = info['assets'][0]['browser_download_url']

    logging.info('Current version: %s', current)
    logging.info('Release version: %s', version)

    if version == current:
        logging.info("Already up to date")
        return

    logging.info("Downloading from %s", downloadurl)
    binary = retrieve(downloadurl)

    if os.path.exists(_tmpfile):
        os.unlink(_tmpfile)

    try:
        with open(_tmpfile,'wb') as f:
            logging.info('Writing %s (%s bytes)', _tmpfile, len(binary))
            f.write(binary)
        logging.info('Setting permissions on %s to 0755', _tmpfile)
        os.chmod(_tmpfile, 0o755)

    except IOError as err:
        logging.error('IO Error writing to %s: %s', _tmpfile, os.strerror(err.errno or 0))
        sys.exit(10)

    try:
        logging.info('Moving %s to %s', _tmpfile, _target)
        move(_tmpfile, _target)

    except IOError as err:
        logging.error('IO Error moving to %s: %s', _target, os.strerror(err.errno or 0))
        logging.info('Manually move %s to /usr/local/bin or use "sudo %s"', _tmpfile, ' '.join(sys.argv))
        sys.exit(10)
