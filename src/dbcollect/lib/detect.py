import os, re, logging, pwd, grp

from lib.errors import Errors, CustomException, SQLError, OracleNotAvailable, LogonDenied, SQLConnectionError, SQLPlusError, SQLTimeout
from lib.functions import execute, getfile
from lib.sqlplus import sqlplus

def sqlplus_status(args, sid, orahome, connectstring):
    """Get instance status"""
    timeout = 10
    if args.no_timeout:
        timeout = None

    proc     = sqlplus(orahome, sid, connectstring, '/tmp', timeout=timeout)
    out, err = proc.communicate('WHENEVER SQLERROR EXIT SQL.SQLCODE\nSET HEAD OFF PAGES 0\nSELECT STATUS from v$instance;')

    if proc.returncode == 0:
        return out.strip()

    if proc.returncode == 124:
        # timeout command exit code
        raise SQLTimeout

    if proc.returncode == 127:
        # sqlplus executable 
        raise SQLPlusError(Errors.E019, sid, 'rc=127')

    for oerr, msg in re.findall(r'^(ORA-\d+):\s+(.*)', out, re.M):
        """
        Known errors:
        ORA-00942: table or view does not exist
        ORA-01017: invalid username/password; logon denied
        ORA-01033: ORACLE initialization or shutdown in progress
        ORA-01034: ORACLE not available
        ORA-01045: user <user> lacks CREATE SESSION privilege; logon denied
        ORA-12154: TNS:could not resolve the connect identifier specified
        ORA-12514: TNS:listener does not currently know of service requested in connect
        ORA-12528: TNS:listener: all appropriate instances are blocking new connections
        ORA-12537: TNS:connection closed
        ORA-12541: TNS:no listener
        ORA-12543: TNS:destination host unreachable
        ORA-12547, TNS:lost contact
        ORA-28000: The account is locked.
        """
        if oerr == 'ORA-01017':
            # usually happens when using the wrong ORACLE_HOME or incorrect groups, try the next one
            check_dba_group(sid, orahome)
            raise LogonDenied

        if oerr == 'ORA-01034':
            # usually happens when using the wrong ORACLE_HOME, try the next one
            raise OracleNotAvailable

        # Other ORA errors
        raise SQLError(oerr, msg)
    
    logging.debug('sqlplus output:\n%s', out)
    raise SQLConnectionError(Errors.E001, 'SQL*Plus failed without ORA-* error')

def check_dba_group(sid, orahome):
    """Check if current user is member of the OSDBA group"""
    config_c = getfile(os.path.join(orahome, 'rdbms/lib/config.c'))
    if not config_c:
        logging.debug('Reading config.c failed')
        return

    r = re.search(r'^.Ldba_string:\s+.string\s+"(\w+)"', config_c, re.M)
    if not r:
        logging.warning(Errors.W010, sid)
        return
    
    dba_group   = r.group(1)
    user        = pwd.getpwuid(os.getuid()).pw_name
    user_groups = os.getgroups()
    user_gid    = grp.getgrnam(dba_group).gr_gid

    if not user_gid in user_groups:
        logging.warning(Errors.W011, sid, user, dba_group)

def check_orahome(args, orahome):
    """Check if orahome is a valid ORACLE_HOME"""
    crsctl  = os.path.join(orahome, 'bin', 'crsctl')
    sqlplus = os.path.join(orahome, 'bin', 'sqlplus')

    if os.path.isfile(crsctl):
        # This is a grid home
        logging.debug('Skipping %s (is GRID_HOME)', orahome)
        return False

    if not os.path.isfile(sqlplus):
        # This is another oracle_home type (i.e. oraagent) - not usable
        logging.debug('Skipping ORACLE_HOME %s (no sqlplus executable %s)', orahome, sqlplus)
        return False

    return True

def get_orahome(args, sid):
    """Find ORACLE_HOME candidates for instance sid"""
    if args.orahome:
        # Use args first
        for orahome in args.orahome.split(','):
            if check_orahome(args, orahome):
                yield orahome

    if not args.no_oratab:
        # if entry is in oratab, use it
        oratab = getfile('/etc/oratab','/var/opt/oracle/oratab')
        if not oratab:
            logging.error(Errors.E018)

        else:
            r = re.search(r'^{0}:(\S+):[y|Y|n|N]'.format(sid), oratab, re.M)
            if r:
                orahome = r.group(1)
                if check_orahome(args, orahome):
                    yield orahome
            else:
                logging.debug('%s not found in oratab', sid)

    if not args.no_orainv:
        # Alternatively, get all inventory candidates
        orainstloc = getfile('/etc/oraInst.loc','/var/opt/oracle/oraInst.loc')
        if not orainstloc:
            logging.error(Errors.E016)
        else:
            r = re.match(r'inventory_loc=(.*)', orainstloc)
            if r:
                inventory_path = os.path.join(r.group(1), 'ContentsXML/inventory.xml')
                inventory = getfile(inventory_path)
                if not inventory:
                    logging.warning(Errors.E017, inventory_path)

                else:
                    for orahome in re.findall(r"<HOME NAME=\"\S+\"\sLOC=\"(\S+)\"", inventory):
                        if check_orahome(args, orahome):
                            yield orahome
            else:
                logging.error(Errors.E016)

def try_connect(args, sid, connectstring=None):
    orahomes = []
    for orahome in get_orahome(args, sid):
        # Check if orahome is used before on this instance
        if orahome in orahomes:
            logging.debug('%s: Duplicate ORACLE_HOME %s, skipping', sid, orahome)
            continue
        orahomes.append(orahome)

        if connectstring:
            logging.info('%s: Trying %s using connectstring', sid, orahome)
        else:
            logging.info('%s: Trying %s as sysdba', sid, orahome)

        try:
            status = sqlplus_status(args, sid, orahome, connectstring)
            logging.info('%s: status is %s', sid, status)
            return orahome

        except LogonDenied:
            logging.warning(Errors.W012, sid, orahome)

        except OracleNotAvailable:
            logging.warning(Errors.W017, sid, orahome)

        except SQLTimeout:
            logging.warning(Errors.E030, sid, orahome)

        except SQLError as e:
            logging.warning(Errors.W016, sid, orahome, *e.args)

    raise SQLConnectionError(Errors.E027, sid)

def get_instances(args):
    """Gets all running sids with a valid ORACLE_HOME, return (sid, oracle_home) pairs"""
    instances = []
    excluded  = args.exclude.split(',') if args.exclude else []
    included  = args.include.split(',') if args.include else []

    # Check if timeout command works
    try:
        execute('timeout --version')
    except OSError:
        logging.debug('timeout missing')

    if args.logons:
        # Connect to services listed in the connect file
        logging.warning(Errors.W015)
        connects = open(args.logons).read()
        for connectstring in re.findall(r'^(\w+\/\S+@\S+/\S+)', connects, re.M):
            r = re.match(r'^\w+\/\S+@\S+/(\S+)', connectstring)
            if not r:
                raise CustomException(Errors.E043, args.connect)

            sid = r.group(1)
            orahome = try_connect(args, sid, connectstring)
            instances.append((sid, orahome, connectstring))

    else:
        # get all sids and try to connect
        logging.info('Detecting running Oracle instances')
        ps_out, _, _ = execute('ps -eo pid,user,group,args')
        for pid, user, group, sid in re.findall(r'(\d+)\s+(\w+)\s+(\w+)\s+ora_pmon_(.*)', ps_out):
            logging.info('Detected running instance %s, pid=%s, user=%s, group=%s', sid, pid, user, group)
            if sid in excluded:
                logging.warning(Errors.W013, sid)
                continue

            elif included and not sid in included:
                logging.warning(Errors.W014, sid)
                continue

            orahome = try_connect(args, sid)
            instances.append((sid, orahome, None))

        instlist = [x[0] for x in instances]
        logging.info('Instances detected: %s', ', '.join(instlist))

    return instances
                