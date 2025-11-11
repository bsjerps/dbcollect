"""
instance.py - Manage Oracle database instances for DBCollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import json, re, logging

from lib.functions import getscript
from lib.errors import Errors, ReportingError, SQLPlusError
from lib.sqlplus import sqlplus

class Job():
    """AWR/Statspack job definition"""
    def __init__(self, reptype, sid, dbid, instnum, beginsnap, endsnap, begintime, endtime):
        self.reptype   = reptype
        self.sid       = sid
        self.dbid      = dbid
        self.instnum   = instnum
        self.beginsnap = beginsnap
        self.endsnap   = endsnap
        self.begintime = begintime
        self.endtime   = endtime

    @property
    def filename(self):
        """Return the filename to be stored in the archive"""
        ext = 'html' if self.reptype == 'awr' else 'txt'
        return '{0}_{1}_{2}_{3}_{4}_{5}_{6}.{7}'.format(self.sid, self.dbid, self.instnum, self.reptype, self.beginsnap, self.endsnap, self.begintime, ext)

    @property
    def query(self):
        """Return the SQLPlus query to generate the AWR or Statspack report"""
        if self.reptype == 'sp':
            return 'set term off escape off\ndefine begin_snap={beginsnap}\ndefine end_snap={endsnap}\ndefine report_name={filename}\n@?/rdbms/admin/spreport'.format(
                beginsnap=self.beginsnap, endsnap=self.endsnap, filename=self.filename)

        return 'SELECT output FROM table (dbms_workload_repository.awr_report_html({dbid},{inst},{beginsnap},{endsnap}));\n'.format(
            dbid=self.dbid, inst=self.instnum, beginsnap=self.beginsnap, endsnap=self.endsnap)

class Instance():
    """Oracle Instance with SQL*Plus, scripts and other methods"""
    def __init__(self, tempdir, sid, orahome, connectstring):
        self.tempdir   = tempdir
        self.sid       = sid
        self.orahome   = orahome
        self.connect   = connectstring
        self.jobs      = []
        self.scripts   = {}
        self.meta_txt  = self.script('meta')
        try:
            # extract the json part (prevent glogin.sql problems)
            r    = re.match(r'.*?(^{.*?^})', self.meta_txt, re.M | re.S)
            meta = r.group(1)
            self.meta = json.loads(meta)
        except Exception as e:
            logging.debug(e)
            logging.debug('meta.sql output:\n%s', self.meta_txt)
            raise SQLPlusError(Errors.E026, self.sid)

        self.meta['oracle_home'] = orahome
        self.meta['oracle_sid']  = self.sid

        self.status    = self.meta['status']
        self.version   = self.meta['version_major']
        self.awrusage  = self.meta.pop('awrusage', 0)
        self.spusage   = self.meta.pop('statspack', 0)
        self.cpus      = self.meta['cpus']

    def sqlplus(self, quiet=False):
        """Create SQL*Plus session and initialize with header"""
        proc = sqlplus(self.orahome, self.sid, self.connect, self.tempdir, quiet=quiet)
        proc.stdin.write("SET tab off feedback off verify off heading off lines 32767 pages 0 trims on\n")
        proc.stdin.write("alter session set nls_date_language=american;\n")

        # Handle Bug 19033356 - SQLPLUS WHENEVER OSERROR FAILS REGARDLESS OF OS COMMAND RESULT.
        proc.stdin.write("whenever oserror continue;\n")

        return proc

    def script(self, name, header=None):
        """Run SQL*Plus query and return the output. Log errors if they appear"""
        sql = getscript(name + '.sql')
        proc = self.sqlplus()
        if header:
            proc.stdin.write(header)
        else:
            proc.stdin.write("SET tab off feedback off verify off heading off lines 1000 pages 0 trims on\n")
        out, _ = proc.communicate(sql)
        if proc.returncode:
            logging.debug('SQL*Plus output for query {0}.sql:\n{1}'.format(name, out))
            raise SQLPlusError(Errors.E041, self.sid, proc.returncode)
        return out.strip()

    def get_jobs(self, args):
        """Get the AWR or Statspack parameters and create jobs, return number of jobs"""
        if args.no_awr:
            return 0
        if not self.status == 'OPEN':
            logging.info('Instance {0} not open, continue...'.format(self.sid))
            return 0

        if args.statspack and self.spusage > 0:
            reptype = 'sp'
            logging.info('{0}: Statspack requested'.format(self.sid))

        elif self.awrusage > 0:
            reptype = 'awr'
            logging.info('{0}: AWR usage detected, generating reports '.format(self.sid))

        elif args.force_awr:
            reptype = 'awr'
            logging.warning(Errors.W002, self.sid)

        elif self.spusage > 0:
            reptype = 'sp'
            logging.info('{0}: No awr, Statspack detected'.format(self.sid))

        elif args.ignore_awr:
            logging.warning(Errors.W004, self.sid)
            return 0
        else:
            raise ReportingError(Errors.E021, self.sid)

        inc_rac  = '0' if args.no_rac  else '1'
        inc_stby = '0' if args.no_stby else '1'
        inc_pack = '1' if args.force_awr else '0'
        header = 'define days = {0}\ndefine end_days = {1}\ndefine inc_rac = {2}\ndefine inc_stby = {3}\ndefine inc_pack = {4}\n'.format(args.days, args.end_days, inc_rac, inc_stby, inc_pack)
        if reptype == 'awr':
            data   = self.script('getawrs', header=header)
        elif reptype == 'sp':
            data   = self.script('getsps', header=header)
        else:
            raise ValueError('Bad reporttype', reptype)
        for line in data.splitlines():
            words = line.split(',')
            if not len(words) == 6:
                continue
            job = Job(reptype, self.sid, *words)
            self.jobs.append(job)

    @property
    def num_jobs(self):
        return len(self.jobs)

    def tasks(self, _tasks=None):
        if _tasks == 0:
            # Unlimited, set equal to NUM_CPUS
            return self.cpus
        elif _tasks is None:
            # Set to 50% of NUM_CPUS, max 8
            return max(1, min(8, self.cpus//2))

        # default
        return min(max(1, _tasks), self.cpus)
