import os, re, stat

from lib.functions import execute, listdir
from lib.user import getuser, getgroup
from lib.jsonfile import JSONFile
from lib.compat import load_file

def get_disklist():
    disklist = []
    out, err, rc = execute('lsblk -dno name')
    for dev in out.rstrip().splitlines():
        info = { 'name': dev, 'properties': {} }
        for file in  ['dev', 'device/model','device/rev','device/queue_depth','device/vendor','device/serial','size','queue/scheduler']:
            path = os.path.join('/sys/class/block/{0}/{1}'.format(dev, file))
            var = file.split('/')[-1]
            try:
                data = load_file(path).strip()
                if var in ('queue_depth','size'):
                    data = int(data)
                info[var] = data

            except IOError:
                info[var] = None

        cmd = 'udevadm info -q symlink -n {0}'.format(dev)
        out, err, rc = execute(cmd)
        if rc != 0:
            info['udevadm_cmd'] = { 'command': cmd, 'stdout': out, 'stderr': err, 'rc': rc }

        info['symlinks'] = out.split()
        cmd = 'udevadm info -q property -n {0}'.format(dev)
        out, err, rc = execute(cmd)
        for k, v in re.findall(r'^(\S+)=(.*)', out, re.M):
            info['properties'][k] = v

        disklist.append(info)

    diskinfo = JSONFile()
    diskinfo.set('diskinfo', {'disklist': disklist })
    return diskinfo

def get_blockdevs():
    blockinfo = {}
    for root, _, files in os.walk('/dev'):
        for file in sorted(files):
            path = os.path.join(root, file)
            st = os.stat(path)
            if stat.S_ISBLK(st.st_mode):
                dev = os.path.realpath(path)
                name = os.path.basename(dev)

                if not name in blockinfo:
                    blockinfo[name] = {
                        'major': os.major(st.st_rdev),
                        'minor': os.minor(st.st_rdev),
                        'mode': st.st_mode,
                        'perms': stat.filemode(st.st_mode),
                        'user': getuser(st.st_uid),
                        'group': getgroup(st.st_gid),
                        'path': dev,
                        'links': [],
                        'properties': {}
                    }
                    out, err, rc = execute('udevadm info -q property -n {0}'.format(name))
                    for k, v in re.findall(r'^(\S+)=(.*)', out, re.M):
                        blockinfo[name]['properties'][k] = v

                blockinfo[name]['links'].append(path)

    blockdevs = [blockinfo[name] for name, _ in blockinfo.items()]

    blkinfo = JSONFile()
    blkinfo.set('blockinfo', {'blockdevices': blockdevs} )
    return blkinfo

def get_niclist():
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

    nicinfo = JSONFile()
    nicinfo.set('nicinfo', {'niclist': niclist} )
    return nicinfo
