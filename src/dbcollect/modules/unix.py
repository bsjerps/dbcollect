"""
unix.py - UNIX functions (AIX, Solaris, HP-UX) for dbcollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, logging

from lib.errors import Errors
from lib.compat import load_file, listdir
from lib.jsonfile import JSONPlusDirectories, JSONPlusCommand

def nmon_info(archive, args):
    """Get NMON reports"""
    nmondirs = args.nmon.split(',')
    nmoninfo = JSONPlusDirectories(*nmondirs)
    archive.writestr('nmoninfo.json', nmoninfo.dump())

    for nmondir in nmondirs:
        if not os.path.exists(nmondir):
            logging.error(Errors.E024, nmondir)
            continue
        for file in listdir(nmondir):
            path = os.path.join(nmondir, file)
            data = load_file(path)
            if data[:12] != 'AAA,progname':
                logging.error(Errors.E025, path)
                continue
            archive.store(path)

def sar_info(archive, args):
    """Get UNIX SAR reports (Text format)"""
    if args.no_sar:
        return

    logging.info('Collecting UNIX SAR reports')
    sarpaths = ('/var/adm/sa','/var/log/sa')
    sarinfo  = JSONPlusDirectories(*sarpaths)
    archive.writestr('sarinfo.json', sarinfo.dump())

    for sardir in sarpaths:
        for sarfile in listdir(sardir):
            path = os.path.join(sardir, sarfile)

            if sarfile.startswith('sar'):
                continue

            if sarfile.startswith('sa'):
                df_cpu   = JSONPlusCommand(args, cmd='sar -uf {0}'.format(path))
                df_block = JSONPlusCommand(args, cmd='sar -bf {0}'.format(path))
                df_disk  = JSONPlusCommand(args, cmd='sar -df {0}'.format(path))
                df_swap  = JSONPlusCommand(args, cmd='sar -rf {0}'.format(path))
                archive.writestr('sar/{0}_{1}.jsonp'.format(sarfile, 'cpu'), df_cpu.jsonp())
                archive.writestr('sar/{0}_{1}.jsonp'.format(sarfile, 'block'), df_block.jsonp())
                archive.writestr('sar/{0}_{1}.jsonp'.format(sarfile, 'disk'), df_disk.jsonp())
                archive.writestr('sar/{0}_{1}.jsonp'.format(sarfile, 'swap'), df_swap.jsonp())
