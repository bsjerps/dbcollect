"""
tools.py - Helper tools DBCollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, sys, logging

from lib.compat import strerror, get_pkg_resource, write_file
from lib.errors import Errors
from lib.config import dbinfo_config

def cleanup_archives(args):
    """Cleanup all old dbcollect zip files in the tempdir (default /tmp)"""

    logging.info('Cleaning up old dbcollect archives in %s', args.tempdir)
    for file in os.listdir(args.tempdir):
        if file.startswith('dbcollect-') and file.endswith('.zip'):
            path = os.path.join(args.tempdir, file)
            logging.info('Deleting %s', path)
            try:
                os.unlink(path)
            except OSError as e:
                logging.error(Errors.E004, e.filename, strerror(e.errno))

def run_sql(args):
    """Dump contents of the requested SQL script + header, so it can be executed manually with SQL*Plus"""
    scriptlist = []
    for s in dbinfo_config.values():
        scriptlist += s

    scriptlist = sorted(scriptlist)

    if args.script == 'list':
        for script in scriptlist:
            print(script)
        return

    if not args.script in scriptlist:
        logging.error('Script %s does not exist', args.script)

    try:
        header = get_pkg_resource('sql', 'dbinfo/header.sql')
        sql    = get_pkg_resource('sql', 'dbinfo/{0}'.format(args.script))
        path   = os.path.join(args.tempdir, args.script)

        write_file(path, header + sql + 'exit;\n')
        if not args.quiet:
            print('# Script written to {0}'.format(path))
            print('# Run the following command to execute the query')
            print('# Or run {0} | bash'.format(' '.join(sys.argv)))
            print('sqlplus -S / as sysdba @{0}'.format(path))

    except OSError as e:
        logging.error(Errors.E004, e.filename, strerror(e.errno))

def completions(args):
    """Dump the bash_completions on stdout"""
    txt = get_pkg_resource('lib', 'complete.bash')
    print(txt)
