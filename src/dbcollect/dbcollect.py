#!/usr/bin/env python
"""
dbcollect.py - Retrieve Oracle database and OS config and performance data
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

try:
    import os, sys, logging, platform, argparse
except ImportError as e:
    print(e)
    sys.exit(10)

sys.dont_write_bytecode = True

if sys.version_info[0] == 2 and sys.version_info[1] < 6:
    sys.exit("Requires Python 2.6 or higher, or 3.6 or higher")
elif sys.version_info[0] == 3 and sys.version_info[1] < 6:
    sys.exit("Requires Python 2.6 or higher, or 3.6 or higher")

from lib.config import versioninfo, settings
from lib.log import logsetup
from lib.errors import Errors, CustomException, ErrorHelp
from lib.archive import Archive
from lib.user import switchuser, username, dbuser
from lib.jsonfile import JSONFile, buildinfo
from lib.functions import sudosetup, getfile
from modules.oracle import oracle_info
from modules.syscollect import host_info
from modules.updater import update

def printversion():
    """Show version information"""
    print ('Author:    {0}'.format(versioninfo['author']))
    print ('Copyright: {0}'.format(versioninfo['copyright']))
    print ('License:   {0}'.format(versioninfo['license']))
    print ('Version:   {0}'.format(versioninfo['version']))
    print ('Builddate: {0}'.format(buildinfo['builddate']))
    print ('Buildhash: {0}'.format(buildinfo['buildhash']))

def main():
    parser = argparse.ArgumentParser(usage='dbcollect [options]')
    parser.add_argument("-V", "--version",    action="store_true",        help="Version and copyright info")
    parser.add_argument("-D", "--debug",      action="store_true",        help="Debug (Show errors)")
    parser.add_argument(      "--log",        action="store_true",        help="Dump logfile when finished")
    parser.add_argument("-q", "--quiet",      action="store_true",        help="Suppress output")
    parser.add_argument("-o", "--overwrite",  action="store_true",        help="Overwrite previous zip file")
    parser.add_argument(      "--update",     action="store_true",        help="Check for updates")
    parser.add_argument(      "--sudoers",    action="store_true",        help="Install sudoers file")
    parser.add_argument(      "--no-sudo",    action="store_true",        help="Don't try to run sudo root commands")
    parser.add_argument(      "--filename",   type=str,                   help="output filename, default dbcollect-<hostname>.zip")
    parser.add_argument(      "--tempdir",    type=str, default='/tmp',   help="TEMP directory, default /tmp")
    parser.add_argument("-u", "--user",       type=str,                   help="Switch to user (if run as root)")
    parser.add_argument("-d", "--days",       type=int, default=10,       help="Number of days ago to START collect of AWR data (default 10, max 999)")
    parser.add_argument(      "--end_days",   type=int, default=0,        help="Number of days ago to END AWR collect period, default 0, max 999")
    parser.add_argument(      "--logons",     type=str,                   help="Use logons file", metavar='<file>')
    parser.add_argument(      "--orahome",    type=str,                   help="ORACLE_HOME to run SQL*Plus (comma separated for multiple)", metavar='<dir>')
    parser.add_argument(      "--force-awr",  action="store_true",        help="Run AWR reports even if AWR usage (license) is not detected. Dangerous!")
    parser.add_argument(      "--statspack",  action="store_true",        help="Prefer Statspack reports even if AWR usage is detected")
    parser.add_argument(      "--ignore-awr", action="store_true",        help="Ignore AWR reports for databases that have no previous usage")
    parser.add_argument(      "--strip",      action="store_true",        help="Strip SQL sections from AWR reports")
    parser.add_argument(      "--no-rac",     action="store_true",        help="Generate AWRs for local instance only")
    parser.add_argument(      "--no-stby",    action="store_true",        help="Generate AWRs for primary DB only (ignore standby DB)")
    parser.add_argument(      "--no-awr",     action="store_true",        help="Skip AWR reports")
    parser.add_argument(      "--no-sar",     action="store_true",        help="Skip SAR reports")
    parser.add_argument(      "--no-ora",     action="store_true",        help="Skip Oracle collection")
    parser.add_argument(      "--no-sys",     action="store_true",        help="Skip OS collection")
    parser.add_argument(      "--no-orainv",  action="store_true",        help="Ignore ORACLE_HOMES from Oracle Inventory")
    parser.add_argument(      "--no-oratab",  action="store_true",        help="Ignore ORACLE_HOMES from oratab")
    parser.add_argument(      "--no-timeout", action="store_true",        help="Don't abort on SQL*Plus timeout when detecting instances")
    parser.add_argument(      "--nmon",       type=str,                   help="Where to look for NMON files (comma separated)", metavar='PATH')
    parser.add_argument(      "--include",    type=str,                   help="Include Oracle instances (comma separated)", metavar='INSTANCES')
    parser.add_argument(      "--exclude",    type=str,                   help="Exclude Oracle instances (comma separated)", metavar='INSTANCES')
    parser.add_argument(      "--tasks",      type=int,                   help="Max number of tasks (default 50%% of cpus (up to 8), 0=use all cpus)")
    parser.add_argument(      "--timeout",    type=int, default=10,       help="Timeout (minutes) for SQL statements (default 10)")
    parser.add_argument(      "--error",      type=str,                   help="Get info on error, warning or informational message (i.e., E001)", metavar='<error>')
    args = parser.parse_args()

    if args.update:
        update(versioninfo['version'])
        return
    if args.sudoers:
        sudosetup()
        return
    if args.error:
        ErrorHelp.help(args.error)
        return
    if os.getuid() == 0:
        cmdline = sys.argv[1:]
        cmdline.insert(0, os.path.realpath(sys.argv[0]))
        if args.user:
            switchuser(args.user, cmdline)
        else:
            user = dbuser()
            switchuser(user, cmdline)
        return

    print('dbcollect {0} - collect Oracle AWR/Statspack, database and system info'.format(versioninfo['version']))
    sys.stdout.flush()
    if args.version:
        printversion()
        return

    if args.quiet:
        sys.stdout = open('/dev/null','w')

    if args.filename:
        if not args.filename.endswith('.zip'):
            args.filename += '.zip'
        zippath = os.path.join('/tmp', args.filename)

    else:
        zippath = (os.path.join('/tmp', 'dbcollect-{0}.zip'.format(platform.uname()[1])))

    logpath = settings['logpath']

    try:
        logsetup(args, logpath)
    except Exception as e:
        logging.fatal(Errors.E014, logpath, e)
        sys.exit(15)

    try:
        logging.info('For diagnosing errors, use --error option. More info on https://wiki.dirty-cache.com/DBCollect/Troubleshooting')
        archive = Archive(zippath, args.overwrite)
        osname = getfile('/etc/system-release') or 'Unknown'
        logging.info('dbcollect {0} - database and system info collector'.format(versioninfo['version']))
        logging.info('Python version {0}'.format(platform.python_version()))
        logging.info('OS version is {0}'.format(osname.strip()))
        logging.info('Current user is {0}'.format(username()))
        logging.info('Zip file is {0}'.format(zippath))
        logging.info('Command line is {0}'.format(' '.join(sys.argv)))
        metainfo = JSONFile()
        metainfo.meta()
        archive.writestr('meta.json', metainfo.dump())
        if not args.no_sys:
            host_info(archive, args)
        if not args.no_ora:
            oracle_info(archive, args)
        archive.ok = True
        logging.info('Zip file {0} is created succesfully.'.format(zippath))
        logging.info('Do not modify the {0} zipfile before transferring'.format(zippath))
        logging.info('Upload the unmodified file to https://cloud.sjerps.eu/s/dbcollect or send via an alternative method')
        logging.info("Finished")

    except KeyboardInterrupt:
        logging.fatal(Errors.E002)
        sys.exit(10)

    except CustomException as e:
        logging.error(*e.args)
        logging.info("Aborting")
        sys.exit(50)

    except IOError as e:
        logging.exception(e)
        logging.error(Errors.E012, e.filename, os.strerror(e.errno))
        logging.info("Aborting")
        sys.exit(20)

    except Exception as e:
        logging.exception(Errors.E001, e)
        logging.info("Aborting")
        sys.exit(40)

    finally:
        if args.log and os.path.isfile(logpath):
            with open(logpath) as logfile:
                print("\nLogfile {0}:".format(logpath))
                print(logfile.read())
        try:
            archive.store(logpath, 'dbcollect.log')
            os.unlink(logpath)
        except UnboundLocalError:
            pass

if __name__ == "__main__":
    print('dbcollect must run from a ZipApp package, use https://github.com/outrunnl/dbcollect/releases/latest')
    sys.exit(10)
