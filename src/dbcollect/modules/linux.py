"""
linux.py - Functions to get linux system configuration
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

# pylint: disable=unused-argument

import os, re, stat, logging

from lib.config import linux_config
from lib.errors import Errors
from lib.user import getuser, getgroup
from lib.jsonfile import JSONPlus, JSONPlusDirectories, JSONPlusCommand, JSONPlusFile
from lib.compat import Progress, load_file, execute, listdir

def get_disklist():
    """Get configuration for all disks"""
    disklist = []
    lsblk = execute('lsblk -dno name')
    for dev in lsblk.stdout.rstrip().splitlines():
        info = { 'name': dev, 'properties': {} }
        for file in  ['dev', 'device/model','device/rev','device/queue_depth','device/vendor','device/serial','size','queue/scheduler']:
            path = os.path.join('/sys/class/block/{0}/{1}'.format(dev, file))
            var = file.rpartition('/')[-1]
            try:
                data = load_file(path).strip()
                if var in ('queue_depth','size'):
                    data = int(data)
                info[var] = data

            except IOError:
                info[var] = None

        cmd = 'udevadm info -q symlink -n {0}'.format(dev)
        udevadm = execute(cmd)
        if udevadm.returncode != 0:
            info['udevadm_cmd'] = { 'command': cmd, 'stdout': udevadm.stdout, 'stderr': udevadm.stderr, 'rc': udevadm.returncode }

        info['symlinks'] = udevadm.stdout.split()
        cmd = 'udevadm info -q property -n {0}'.format(dev)
        udevinfo = execute(cmd)
        for k, v in re.findall(r'^(\S+)=(.*)', udevinfo.stdout, re.M):
            info['properties'][k] = v

        disklist.append(info)

    diskinfo = JSONPlus()
    diskinfo.set('diskinfo', {'disklist': disklist })
    return diskinfo

def get_blockdevs():
    """Get configuration for all logical block devices"""
    blockinfo = {}
    for root, _, files in os.walk('/dev'):
        for file in sorted(files):
            path = os.path.join(root, file)
            try:
                st = os.stat(path)
                if not stat.S_ISBLK(st.st_mode):
                    continue

                dev = os.path.realpath(path)
                name = os.path.basename(dev)

                if name not in blockinfo:
                    blockinfo[name] = {
                        'major': os.major(st.st_rdev),
                        'minor': os.minor(st.st_rdev),
                        'mode': st.st_mode,
                        'user': getuser(st.st_uid),
                        'group': getgroup(st.st_gid),
                        'path': dev,
                        'links': [],
                        'properties': {}
                    }
                    udevinfo = execute('udevadm info -q property -n {0}'.format(name))
                    for k, v in re.findall(r'^(\S+)=(.*)', udevinfo.stdout, re.M):
                        blockinfo[name]['properties'][k] = v

                blockinfo[name]['links'].append(path)

            except OSError:
                continue

    blockdevs = [blockinfo[name] for name, _ in blockinfo.items()]

    blkinfo = JSONPlus()
    blkinfo.set('blockinfo', {'blockdevices': blockdevs} )
    return blkinfo

def get_niclist():
    """Get configuration for all network interfaces"""
    niclist = []
    for dev in listdir('/sys/class/net'):
        if dev == 'lo':
            continue

        info = { 'name': dev }
        directory = os.path.join('/sys/class/net', dev)
        if not os.path.isdir(directory):
            continue

        for var in ['mtu', 'speed', 'address','duplex']:
            path = os.path.join(directory, var)
            try:
                data = load_file(path).rstrip()
                if var in ('mtu','speed'):
                    data = int(data)
                info[var] = data

            except  (IOError, OSError):
                info[var] = None

        niclist.append(info)

    nicinfo = JSONPlus()
    nicinfo.set('nicinfo', {'niclist': niclist} )
    return nicinfo

def get_linux_config(archive):
    """Get Linux system configuration"""
    info = {}
    for cmd in ('sestatus','uptime'):
        try:
            completed = execute(cmd)
            if completed.returncode != 0:
                info['{0}_error'.format(cmd)] = { 'command': cmd, 'stdout': completed.stdout, 'stderr': completed.stderr, 'rc': completed.returncode }
            if cmd == 'sestatus':
                out = completed.stdout.split()[-1]
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
                    data = load_file(path)
                    info[file] = data.rstrip()
                except IOError:
                    info[file] = None

    except OSError as e:
        logging.warning(Errors.W006, e)

    hostinfo = JSONPlus()
    hostinfo.set('hostinfo', info)
    archive.writestr('hostinfo.json', hostinfo.dump())

    diskinfo = get_disklist()
    archive.writestr('diskinfo.json', diskinfo.dump())

    nicinfo = get_niclist()
    archive.writestr('nicinfo.json', nicinfo.dump())

    blkinfo = get_blockdevs()
    archive.writestr('blockinfo.json', blkinfo.dump())

def get_linux_sar(args, archive):
    """Get all (binary) SAR files"""
    if args.no_sar:
        return

    logging.info('Collecting Linux SAR files')

    sar_directories = ('/var/log/sa', '/var/log/sysstat')
    sarinfo  = JSONPlusDirectories(*sar_directories)

    try:
        sarversion = execute('sar -V')
        sarinfo.set('sar', { 'version': sarversion.stderr.strip() })

    except OSError:
        logging.warning(Errors.W008)

    archive.writestr('sarinfo.json', sarinfo.dump())

    if os.path.isfile('/usr/bin/systemctl'):
        collect_timer = execute('systemctl is-active --quiet sysstat-collect.timer')
        if collect_timer.returncode != 0:
            logging.warning(Errors.W009)

    for sardir in ('/var/log/sa', '/var/log/sysstat'):
        for sarfile in listdir(sardir):
            path = os.path.join(sardir, sarfile)
            if sarfile.startswith('sa'):
                if sarfile.startswith('sar'):
                    continue
                archive.store(path)

def get_linux_commands(args, archive):
    """Run the non-root commands for the OS specified in the config"""

    lsblk = execute('lsblk -V')
    lsblk_version = (lsblk.stdout).split()[-1]

    progress = Progress(args)

    for tag, cmd in linux_config['commands'].items():
        # filter lsblk depending on the version of util-linux
        if tag == 'lsblk_long' and lsblk_version.startswith('2.1'):
            continue
        if tag == 'lsblk_el6' and not lsblk_version.startswith('2.1'):
            continue

        df = JSONPlusCommand(args, cmd=cmd, progress=progress)
        archive.writestr('cmd/{0}.jsonp'.format(tag), df.jsonp())

def get_linux_files(args, archive):
    """Get linux files from configuration"""

    progress = Progress(args)
    for file in linux_config['files']:
        df = JSONPlusFile(progress=progress, path=file)
        archive.writestr(file + '.jsonp', df.jsonp())

def get_linux_udev(args, archive):
    """Get udev rules files"""

    progress = Progress(args)
    for file in listdir('/etc/udev/rules.d/'):
        path = os.path.join('/etc/udev/rules.d/', file)
        if os.path.isfile(path) and file.endswith('.rules'):
            df = JSONPlusFile(path=path, progress=progress)
            archive.writestr(path + '.jsonp', df.jsonp())
