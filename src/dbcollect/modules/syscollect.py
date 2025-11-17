"""
syscollect.py - OS and system functions for dbcollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, re, platform, logging
from lib.config import aix_config, sunos_config, hpux_config
from lib.jsonfile import JSONPlusCommand, JSONPlusFile
from lib.errors import Errors
from lib.compat import execute
from modules.unix import nmon_info, sar_info
from modules.linux import get_linux_config, get_linux_sar, get_linux_commands, get_linux_files, get_linux_udev

def host_info(archive, args):
    """Get OS and run the corresponding OS/SAR module"""
    system = platform.system()
    logging.info('Collecting OS info ({0})'.format(system))

    if args.nmon:
        nmon_info(archive, args)

    if system == 'Linux':
        linux_info(archive, args)

    elif system == 'AIX':
        aix_info(archive, args)

    elif system == 'SunOS':
        sun_info(archive, args)

    elif system == 'HP-UX':
        hpux_info(archive, args)

    else:
        # Check to continue even if platform is unknown?
        logging.error(Errors.E008, system)

def linux_info(archive, args):
    """System/SAR info for Linux"""

    get_linux_config(archive)
    get_linux_commands(args, archive)
    get_linux_files(args, archive)
    get_linux_udev(args, archive)
    get_linux_sar(args, archive)

def aix_info(archive, args):
    """System/SAR info for AIX (pSeries)"""
    logging.info('Collecting AIX System info')

    for tag, cmd in aix_config['commands'].items():
        df = JSONPlusCommand(args, cmd=cmd)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    for file in aix_config['files']:
        df = JSONPlusFile(path=file)
        archive.writestr(file + '.jsonp', df.jsonp())

    lsdev = execute('lsdev -Cc disk -Fname')
    ifcfg = execute('ifconfig -l')
    lsvg  = execute('lsvg')

    logging.info('Collecting AIX Disk info')
    for disk in lsdev.stdout.splitlines():
        df_size = JSONPlusCommand(args, cmd='getconf DISK_SIZE /dev/{0}'.format(disk))
        df_cfg  = JSONPlusCommand(args, cmd='lscfg -vpl {0}'.format(disk))
        df_path = JSONPlusCommand(args, cmd='lspath -l {0} -F parent,status'.format(disk))
        df_attr = JSONPlusCommand(args, cmd='lsattr -El {0}'.format(disk))
        archive.writestr('disk/{0}_disksize.jsonp'.format(disk), df_size.jsonp())
        archive.writestr('disk/{0}_lscfg.jsonp'.format(disk), df_cfg.jsonp())
        archive.writestr('disk/{0}_lspath.jsonp'.format(disk), df_path.jsonp())
        archive.writestr('disk/{0}_lsattr.jsonp'.format(disk), df_attr.jsonp())

    logging.info('Collecting AIX Network info')
    for nic in ifcfg.stdout.split():
        if nic.startswith('lo'):
            continue
        df_attr = JSONPlusCommand(args, cmd='lsattr -E -l {0} -F description,value'.format(nic))
        df_stat = JSONPlusCommand(args, cmd='entstat -d {0}'.format(nic))
        archive.writestr('nic/{0}_lsattr.jsonp'.format(nic), df_attr.jsonp())
        archive.writestr('nic/{0}_entstat.jsonp'.format(nic), df_stat.jsonp())

    logging.info('Collecting AIX LVM info')
    for vg in lsvg.stdout.splitlines():
        df_lvs =  JSONPlusCommand(args, cmd='lsvg -l {0}'.format(vg))
        df_pvs =  JSONPlusCommand(args, cmd='lsvg -p {0}'.format(vg))
        archive.writestr('lvm/{0}_lvs.jsonp'.format(vg), df_lvs.jsonp())
        archive.writestr('lvm/{0}_pvs.jsonp'.format(vg), df_pvs.jsonp())

    sar_info(archive, args)

def sun_info(archive, args):
    """System/SAR info for Sun Solaris (SPARC or Intel)"""
    logging.info('Collecting Solaris System info')
    for tag, cmd in sunos_config['commands'].items():
        df = JSONPlusCommand(args, cmd=cmd)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    for file in sunos_config['files']:
        df = JSONPlusFile(path=file)
        archive.writestr(file + '.jsonp', df.jsonp())

    sar_info(archive, args)

def hpux_info(archive, args):
    """System/SAR info for HP-UX (Itanium)"""
    logging.info('Collecting HP-UX System info')
    for tag, cmd in hpux_config['commands'].items():
        df = JSONPlusCommand(args, cmd=cmd)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    for tag, cmd in hpux_config['rootcommands'].items():
        df = JSONPlusCommand(args, cmd=cmd, sudo=True)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    for file in hpux_config['files']:
        df = JSONPlusFile(path=file)
        archive.writestr(file + '.jsonp', df.jsonp())

    logging.info('Collecting HP-UX Disk info')
    disks = []
    ioscan = execute('ioscan -funNC disk')
    for disk, rest in re.findall(r'^\s+(/dev/disk/\S+)\s+(.*)', ioscan.stdout, re.M):
        rdisks = rest.split()
        for disk in rdisks:
            if re.match(r'/dev/rdisk/disk\d+$', disk):
                disks.append(disk)

    for dev in disks:
        disk = os.path.basename(dev)
        cmd = '/usr/sbin/diskinfo {0}'.format(dev)
        diskinfo = JSONPlusCommand(args, cmd=cmd, sudo=True)
        archive.writestr('cmd/diskinfo_{0}.jsonp'.format(disk), diskinfo.jsonp())

    sar_info(archive, args)
