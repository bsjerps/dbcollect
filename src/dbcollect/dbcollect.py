#!/usr/bin/env python
"""
dbcollect.py - Retrieve Oracle database and OS config and performance data
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""
import sys

try:
    import logging, argparse
    from lib.compat import check_python_version
    check_python_version()

    from lib.config import versioninfo
    from lib.errors import ErrorHelp, DBWorkerFailed
    from lib.jsonfile import buildinfo
    from modules.collector import collect_wrapper
    from modules.updater import update

except ImportError as e:
    print(e)
    sys.exit(10)

sys.dont_write_bytecode = True

logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s: %(message)s", datefmt='%Y-%m-%d %I:%M:%S')

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
    parser.add_argument("-q", "--quiet",      action="store_true",        help="Suppress output")
    parser.add_argument("-u", "--user",       type=str,                   help="Switch to user (if run as root)")
    parser.add_argument(      "--filename",   type=str,                   help="output filename, default dbcollect-<hostname>.zip")
    parser.add_argument(      "--update",     action="store_true",        help="Check for updates")
    parser.add_argument(      "--tempdir",    type=str, default='/tmp',   help="TEMP directory, default /tmp")
    parser.add_argument("-d", "--days",       type=int, default=10,       help="Number of days ago to START collect of AWR data (default 10, max 999)")
    parser.add_argument(      "--end_days",   type=int, default=0,        help="Number of days ago to END AWR collect period, default 0, max 999")
    parser.add_argument(      "--logons",     type=str,                   help="Use logons file", metavar='<file>')
    parser.add_argument(      "--orahome",    type=str,                   help="ORACLE_HOME to run SQL*Plus (comma separated for multiple)", metavar='<dir>')
    parser.add_argument(      "--force-awr",  action="store_true",        help="Run AWR reports even if AWR usage (license) is not detected. Diagnostics Pack required!")
    parser.add_argument(      "--statspack",  action="store_true",        help="Prefer Statspack reports even if AWR usage is detected")
    parser.add_argument(      "--ignore-awr", action="store_true",        help="Ignore AWR reports for databases that have no previous usage. Avoid where possible!")
    parser.add_argument(      "--strip",      action="store_true",        help="Strip SQL sections from AWR reports")
    parser.add_argument(      "--no-rac",     action="store_true",        help="Generate AWRs for local instance only (then run dbcollect on all nodes)")
    parser.add_argument(      "--no-stby",    action="store_true",        help="Generate AWRs for primary DB only (ignore standby DB)")
    parser.add_argument(      "--no-awr",     action="store_true",        help="Skip AWR reports")
    parser.add_argument(      "--no-sar",     action="store_true",        help="Skip SAR reports")
    parser.add_argument(      "--no-ora",     action="store_true",        help="Skip Oracle collection")
    parser.add_argument(      "--no-sys",     action="store_true",        help="Skip System info collection")
    parser.add_argument(      "--no-root",    action="store_true",        help="Skip root commands (even if we are root)")
    parser.add_argument(      "--no-acct",    action="store_true",        help="Skip process accounting collection")
    parser.add_argument(      "--no-orainv",  action="store_true",        help="Ignore ORACLE_HOMES from Oracle Inventory")
    parser.add_argument(      "--no-oratab",  action="store_true",        help="Ignore ORACLE_HOMES from oratab")
    parser.add_argument(      "--no-timeout", action="store_true",        help="Don't abort on SQL*Plus timeout when detecting instances")
    parser.add_argument(      "--nmon",       type=str,                   help="Where to look for NMON files (comma separated)", metavar='PATH')
    parser.add_argument(      "--skip-sql",   type=str,                   help="Skip SQL scripts (comma separated)", metavar='SCRIPTS')
    parser.add_argument(      "--skip-cmd",   type=str,                   help="Skip OS commands (comma separated)", metavar='COMMANDS')
    parser.add_argument(      "--include",    type=str,                   help="Include Oracle instances (comma separated)", metavar='INSTANCES')
    parser.add_argument(      "--exclude",    type=str,                   help="Exclude Oracle instances (comma separated)", metavar='INSTANCES')
    parser.add_argument(      "--tasks",      type=int,                   help="Max number of tasks (default 50%% of cpus (up to 8), 0=use all cpus)")
    parser.add_argument(      "--timeout",    type=int, default=10,       help="Timeout (minutes) for SQL statements (default 10)")
    parser.add_argument(      "--error",      type=str,                   help="Get info on error, warning or informational message (i.e., E001)", metavar='<error>')
    args = parser.parse_args()

    if not args.quiet:
        print('dbcollect {0} - collect Oracle AWR/Statspack, database and system info'.format(versioninfo['version']))
        sys.stdout.flush()

    if args.version:
        printversion()

    elif args.update:
        update(versioninfo['version'])

    elif args.error:
        ErrorHelp.help(args.error)

    else:
        try:
            collect_wrapper(args)

        except KeyboardInterrupt:
            logging.critical('Aborted')

        except DBWorkerFailed as e:
            logging.debug(e)
            logging.critical("Aborting")
            sys.exit(50)

if __name__ == "__main__":
    print('dbcollect must run from a ZipApp package, use https://github.com/outrunnl/dbcollect/releases/latest')
    sys.exit(10)
