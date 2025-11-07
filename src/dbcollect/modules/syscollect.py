"""
syscollect.py - OS and system functions for dbcollect
Copyright (c) 2024 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, re, platform, logging
from lib.config import linux_config, aix_config, sunos_config, hpux_config
from lib.jsonfile import JSONFile
from lib.functions import execute, listdir
from lib.errors import Errors
from modules.linux import get_blockdevs, get_disklist, get_niclist

# Check to continue even if platform is unknown?
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
        logging.error(Errors.E008, system)

def nmon_info(archive, args):
    """Get NMON reports"""
    nmondirs = args.nmon.split(',')
    nmoninfo = JSONFile()
    nmoninfo.dir(*nmondirs)
    archive.writestr('nmoninfo.json', nmoninfo.dump())

    for nmondir in nmondirs:
        if not os.path.exists(nmondir):
            logging.error(Errors.E024, nmondir)
            continue
        for file in listdir(nmondir):
            path = os.path.join(nmondir, file)
            with open(path) as f:
                buf = f.read(12)
                if buf != 'AAA,progname':
                    logging.error(Errors.E025, path)
                    continue
            archive.store(path)

def sar_info(archive, args):
    """Get UNIX SAR reports"""
    if args.no_sar:
        return
    logging.info('Collecting UNIX SAR reports')
    sarpath = '/var/adm/sa'
    sarinfo = JSONFile()
    sarinfo.dir(sarpath)
    archive.writestr('sarinfo.json', sarinfo.dump())

    for sarfile in listdir(sarpath):
        path = os.path.join(sarpath, sarfile)
        if sarfile.startswith('sar'):
            continue
        if sarfile.startswith('sa'):
            df_cpu   = JSONFile(cmd='sar -uf {0}'.format(path))
            df_block = JSONFile(cmd='sar -bf {0}'.format(path))
            df_disk  = JSONFile(cmd='sar -df {0}'.format(path))
            df_swap  = JSONFile(cmd='sar -rf {0}'.format(path))
            archive.writestr('sar/{0}_{1}.jsonp'.format(sarfile, 'cpu'), df_cpu.jsonp())
            archive.writestr('sar/{0}_{1}.jsonp'.format(sarfile, 'block'), df_block.jsonp())
            archive.writestr('sar/{0}_{1}.jsonp'.format(sarfile, 'disk'), df_disk.jsonp())
            archive.writestr('sar/{0}_{1}.jsonp'.format(sarfile, 'swap'), df_swap.jsonp())

def linux_info(archive, args):
    """System/SAR info for Linux"""
    info = {}
    for cmd in ('sestatus','uptime'):
        try:
            out, err, rc = execute(cmd)
            if rc != 0:
                info['{0}_error'.format(cmd)] = { 'command': cmd, 'stdout': out, 'stderr': err, 'rc': rc }
            if cmd == 'sestatus':
                out = out.split()[-1]
            info[cmd] = out.strip()

        except OSError as e:
            info[cmd] = None
            logging.warning(Errors.W005, cmd, e)

    try:
        for file in os.listdir('/sys/class/dmi/id'):
            if file in ('modalias','uevent'):
                continue
            path = os.path.join('/sys/class/dmi/id', file)
            if os.path.isfile(path):
                try:
                    with open(path) as f:
                        data = f.read()
                        info[file] = data.rstrip()
                except IOError:
                    info[file] = None

    except OSError as e:
        logging.warning(Errors.W006, e)

    hostinfo = JSONFile()
    hostinfo.set('hostinfo', info)
    archive.writestr('hostinfo.json', hostinfo.dump())

    # TODO:
    # powerpath / scaleio? -> Need root?

    diskinfo = get_disklist()
    archive.writestr('diskinfo.json', diskinfo.dump())

    nicinfo = get_niclist()
    archive.writestr('nicinfo.json', nicinfo.dump())

    blkinfo = get_blockdevs()
    archive.writestr('blockinfo.json', blkinfo.dump())

    out, err, rc = execute('lsblk -V')
    lsblk_version = (out + err).split()[-1]

    for tag, cmd in linux_config['commands'].items():
        if tag == 'lsblk_long' and lsblk_version.startswith('2.1'):
            continue
        if tag == 'lsblk_el6' and not lsblk_version.startswith('2.1'):
            continue

        df = JSONFile(cmd=cmd)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    if not args.no_sudo:
        jc = JSONFile(cmd='sudo -n -l')
        archive.writestr('cmd/sudo_nl.jsonp', jc.jsonp())

        sudo_failed  = []
        for tag, cmd in linux_config['rootcommands'].items():
            df = JSONFile(cmd=cmd, sudo=True)
            if df.errors.startswith('sudo'):
                sudo_failed.append('"{0}"'.format(cmd.split()[0]))

            archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

        if sudo_failed:
            logging.info('Blocked sudo commands: %s', ', '.join(set(sudo_failed)))

    for file in linux_config['files']:
        df = JSONFile(path=file)
        archive.writestr(file + '.jsonp', df.jsonp())

    for file in listdir('/etc/udev/rules.d/'):
        path = os.path.join('/etc/udev/rules.d/', file)
        if os.path.isfile(path) and file.endswith('.rules'):
            df = JSONFile(path=path)
            archive.writestr(path + '.jsonp', df.jsonp())

    if not args.no_sar:
        logging.info('Collecting Linux SAR files')

        try:
            out, err, rc = execute('rpm -q --quiet sysstat')
            if rc != 0:
                logging.warning(Errors.W008)

        except OSError:
            pass

        if os.path.isfile('/usr/bin/systemctl'):
            out, err, rc = execute('systemctl is-active --quiet sysstat-collect.timer')
            if rc != 0:
                logging.warning(Errors.W009)                    

        sarinfo = JSONFile()
        sardirs = ('/var/log/sa', '/var/log/sysstat')
        sarinfo.dir(*sardirs)
        archive.writestr('sarinfo.json', sarinfo.dump())
        for sardir in sardirs:
            for sarfile in listdir(sardir):
                path = os.path.join(sardir, sarfile)
                if sarfile.startswith('sa'):
                    if sarfile.startswith('sar'):
                        continue
                    archive.store(path)

def aix_info(archive, args):
    """System/SAR info for AIX (pSeries)"""
    logging.info('Collecting AIX System info')

    for tag, cmd in aix_config['commands'].items():
        df = JSONFile(cmd=cmd)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    for file in aix_config['files']:
        df = JSONFile(path=file)
        archive.writestr(file + '.jsonp', df.jsonp())

    disks, _, _ = execute('lsdev -Cc disk -Fname')
    nics, _, _ = execute('ifconfig -l')
    vgs, _, _ =  execute('lsvg')

    logging.info('Collecting AIX Disk info')
    for disk in disks.splitlines():
        df_size = JSONFile(cmd='getconf DISK_SIZE /dev/{0}'.format(disk))
        df_cfg  = JSONFile(cmd='lscfg -vpl {0}'.format(disk))
        df_path = JSONFile(cmd='lspath -l {0} -F parent,status'.format(disk))
        df_attr = JSONFile(cmd='lsattr -El {0}'.format(disk))
        archive.writestr('disk/{0}_disksize.jsonp'.format(disk), df_size.jsonp())
        archive.writestr('disk/{0}_lscfg.jsonp'.format(disk), df_cfg.jsonp())
        archive.writestr('disk/{0}_lspath.jsonp'.format(disk), df_path.jsonp())
        archive.writestr('disk/{0}_lsattr.jsonp'.format(disk), df_attr.jsonp())

    logging.info('Collecting AIX Network info')
    for nic in nics.split():
        if nic.startswith('lo'):
            continue
        df_attr = JSONFile(cmd='lsattr -E -l {0} -F description,value'.format(nic))
        df_stat = JSONFile(cmd='entstat -d {0}'.format(nic))
        archive.writestr('nic/{0}_lsattr.jsonp'.format(nic), df_attr.jsonp())
        archive.writestr('nic/{0}_entstat.jsonp'.format(nic), df_stat.jsonp())

    logging.info('Collecting AIX LVM info')
    for vg in vgs.splitlines():
        df_lvs =  JSONFile(cmd='lsvg -l {0}'.format(vg))
        df_pvs =  JSONFile(cmd='lsvg -p {0}'.format(vg))
        archive.writestr('lvm/{0}_lvs.jsonp'.format(vg), df_lvs.jsonp())
        archive.writestr('lvm/{0}_pvs.jsonp'.format(vg), df_pvs.jsonp())

    sar_info(archive, args)

def sun_info(archive, args):
    """System/SAR info for Sun Solaris (SPARC or Intel)"""
    logging.info('Collecting Solaris System info')
    for tag, cmd in sunos_config['commands'].items():
        df = JSONFile(cmd=cmd)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    for file in sunos_config['files']:
        df = JSONFile(path=file)
        archive.writestr(file + '.jsonp', df.jsonp())

    sar_info(archive, args)

def hpux_info(archive, args):
    """System/SAR info for HP-UX (Itanium)"""
    logging.info('Collecting HP-UX System info')
    for tag, cmd in hpux_config['commands'].items():
        df = JSONFile(cmd=cmd)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    for tag, cmd in hpux_config['rootcommands'].items():
        df = JSONFile(cmd=cmd, sudo=True)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

    for file in hpux_config['files']:
        df = JSONFile(path=file)
        archive.writestr(file + '.jsonp', df.jsonp())

    logging.info('Collecting HP-UX Disk info')
    disks = []
    ioscan, err, rc = execute('ioscan -funNC disk')
    for disk, rest in re.findall(r'^\s+(/dev/disk/\S+)\s+(.*)', ioscan, re.M):
        rdisks = rest.split()
        for disk in rdisks:
            if re.match(r'/dev/rdisk/disk\d+$', disk):
                disks.append(disk)

    for dev in disks:
        disk = os.path.basename(dev)
        cmd = '/usr/sbin/diskinfo {0}'.format(dev)
        diskinfo = JSONFile(cmd=cmd, sudo=True)
        archive.writestr('cmd/diskinfo_{0}.jsonp'.format(disk), diskinfo.jsonp())

    sar_info(archive, args)
