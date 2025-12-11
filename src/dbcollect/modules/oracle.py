"""
oracle.py - Oracle functions for DBCollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

import os, logging, time
from datetime import timedelta
from multiprocessing import Process

from lib.errors import Errors, CustomException
from lib.detect import get_instances
from lib.multiproc import Shared, Tempdir
from lib.jsonfile import JSONPlusCommand
from lib.compat import Progress
from .awrstrip import awrstrip
from .instance import Instance
from .workers import job_generator, job_processor, info_processor

def oracle_info(archive, args):
    """Collect Oracle config and workload data"""
    logging.info('Collecting Oracle info')
    td         = Tempdir(args)
    tempdir    = td.tempdir
    instances  = []
    total_jobs = 0
    done_jobs  = 0
    orahomes   = []

    for sid, orahome, connectstring in get_instances(args):
        orahomes.append(orahome)
        instance = Instance(tempdir, sid, orahome, connectstring)
        instance.get_jobs(args)
        total_jobs += instance.num_jobs
        logging.info('{0}: generating {1} workload reports'.format(sid, instance.num_jobs))
        instances.append(instance)

    for i, orahome in enumerate(sorted(set(orahomes))):
        # Get ORACLE_HOME patch info
        lspatches_cmd = '{0} lspatches'.format(os.path.join(orahome, 'OPatch/opatch'))
        listener_cmd  = '{0} status'.format(os.path.join(orahome, 'bin/lsnrctl'))

        jp = JSONPlusCommand(args, cmd=lspatches_cmd)
        archive.writestr('oracle/orahome_{0}/lspatches.jsonp'.format(i+1), jp.jsonp())

        # Get Listener services
        jp = JSONPlusCommand(args, cmd=listener_cmd, ORACLE_HOME=orahome)
        archive.writestr('oracle/orahome_{0}/listener.jsonp'.format(i+1), jp.jsonp())

    msg = 'No reports'
    starttime = time.time()
    for instance in instances:
        shared    = Shared(args, instance, tempdir)
        dbidir    = os.path.join(tempdir, 'dbinfo')
        dbldir    = os.path.join(tempdir, 'log')
        awrdir    = os.path.join(tempdir, 'awr')
        workers   = []

        info_processor(shared)

        progress = Progress(args)

        generator = Process(target=job_generator, name='Generator', args=(shared,))
        generator.start()
        num_tasks = instance.tasks(args.tasks)
        for i in range(num_tasks):
            worker = Process(target=job_processor, name='Processor', args=(shared,i))
            worker.start()
            workers.append(worker)

        logging.info('%s: Started %s SQLPlus sessions', shared.instance.sid, len(workers))

        while True:
            # Pick up completed AWR or Statspack files and move them to the archive
            time.sleep(1)
            filelist = os.listdir(awrdir)
            working  = any([worker.is_alive() for worker in workers])

            # Break if no more files AND no more workers
            if not any((filelist, working)):
                break

            for filename in filelist:
                path = os.path.join(awrdir, filename)

                # If requested, strip HTML file from SQL sections
                if args.strip and filename.endswith('.html'):
                    awrstrip(path, inplace=True)
                    logging.debug('Stripped SQL code from {0}'.format(filename))

                # Store the file and remove from FS
                archive.store(path, 'oracle/{0}/'.format(instance.sid) + filename)
                os.unlink(path)

                # Housekeeping
                done_jobs += 1
                pct_done   = float(done_jobs)/total_jobs
                elapsed    = time.time() - starttime
                rps        = done_jobs/elapsed
                eta        = (total_jobs - done_jobs)*elapsed/done_jobs
                elapsed_s  = timedelta(seconds=round(elapsed))
                eta_s      = timedelta(seconds=round(eta))
                msg = 'Report {0} of {1} ({2:.1%} done), elapsed: {3}, remaining: {4}, reports/s: {5:.2f}'.format(
                        done_jobs, total_jobs, pct_done, elapsed_s, eta_s, rps)

                progress.message(msg, debug=False)

        for worker in workers:
            worker.join()
            if worker.exitcode == 20:
                # SQLError or SQLTimeout, already logged
                pass
            elif worker.exitcode:
                logging.error(Errors.E022, worker.exitcode)

        progress.clear()
        logging.info('%s: Workers completed', instance.sid)

        # Clean hanging jobs
        while not shared.jobs.empty():
            _ = shared.jobs.get()
            time.sleep(0.001)

        logging.debug('%s: Waiting for job generator', instance.sid)
        generator.join()
        logging.info('%s: Job generator completed', instance.sid)

        # Pick up DBInfo and Log files
        for filename in os.listdir(dbidir):
            path = os.path.join(dbidir, filename)
            archive.store(path, 'oracle/dbinfo/{0}'.format(filename))
            os.unlink(path)

        for filename in os.listdir(dbldir):
            path = os.path.join(dbldir, filename)
            archive.store(path, 'oracle/log/{0}'.format(filename))
            os.unlink(path)

        if any([worker.exitcode for worker in workers]):
            raise CustomException(Errors.E039, instance.sid)

        if generator.exitcode:
            raise CustomException(Errors.E023, generator.exitcode)

    logging.info(msg)
