"""
errors.py - Exception subclasses for DBCollect
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+
"""

# pylint: disable=line-too-long,unused-variable


class LogonDenied(Exception):
    pass

class OracleNotAvailable(Exception):
    pass

class DBWorkerFailed(Exception):
    pass

class DBCollectFailed(Exception):
    pass

class CustomException(Exception):
    pass

class ReportingError(CustomException):
    pass

class SQLPlusError(CustomException):
    pass

class SQLConnectionError(CustomException):
    pass

class SQLError(CustomException):
    pass

class SQLTimeout(CustomException):
    pass

class InstanceNotAvailable(CustomException):
    pass

class Errors():
    """
    Info, Warning and Error messages
    """
    W001 = "[DBC-W001] Subprocess %s interrupted"
    W002 = "[DBC-W002] %s: No prior AWR usage detected, continuing anyway (--force-awr)"
    W003 = "[DBC-W003] Writing data to zip file failed: %s (%s)"
    W004 = "[DBC-W004] Skipping %s: No prior AWR usage or Statspack detected (--ignore)"
    W005 = "[DBC-W005] Executing %s failed (%s)"
    W006 = "[DBC-W006] Reading DMI info failed (%s)"
    W007 = "[DBC-W007] Skipping %s: disabled in credentials file"
    W008 = "[DBC-W008] sysstat not installed, not collecting OS performance data"
    W009 = "[DBC-W009] sysstat timer not active, not collecting OS performance data"
    W010 = "[DBC-W010] %s: Cannot parse ORACLE_HOME/rdbms/lib/config.c"
    W011 = "[DBC-W011] %s: User %s is not a member of group %s"
    W012 = "[DBC-W012] %s: Logon denied (ORA-01017), skipping %s"
    W013 = "[DBC-W013] %s: skipping (excluded)"
    W014 = "[DBC-W014] %s: skipping (not included)"
    W015 = "[DBC-W015] Using only connectstrings (skipping local instances detection)"
    W016 = "[DBC-W016] %s: (%s) SQL*Plus Error %s, %s"
    W017 = "[DBC-W017] %s: Oracle not available (ORA-01034), skipping %s"

    E001 = "[DBC-E001] Unknown error: %s, see logfile for debug info"
    E002 = "[DBC-E002] Keyboard interrupt, Aborting..."
    E003 = "[DBC-E003] Cannot create zipfile %s"
    E004 = "[DBC-E004] OS error retrieving %s: %s"
    E005 = "[DBC-E005] IO error retrieving %s: %s"
    E006 = "[DBC-E006] HTML Parsing error in %s, not stripped"
    E007 = "[DBC-E007] I/O error writing %s: %s"
    E008 = "[DBC-E008] Unknown platform %s"
    E009 = "[DBC-E009] %s: Worker terminated (pid=%s, rc=%s) running SQLPlus script %s"
    E010 = "[DBC-E010] %s: Timeout (pid=%s, %s seconds) running SQLPlus script %s"
    E011 = "[DBC-E011] %s: Generator timeout (queue full, %s seconds)"
    E012 = "[DBC-E012] I/O error in %s: %s"
    E013 = "[DBC-E013] Exception in %s: %s"
    E014 = "[DBC-E014] Cannot create logfile %s (%s)"
    E015 = "[DBC-E015] Unknown error reading file %s (%s)"
    E016 = "[DBC-E016] oraInst.loc not found or readable"
    E017 = "[DBC-E017] inventory.xml not found or readable: %s"
    E018 = "[DBC-E018] oratab not found or readable"
    E019 = "[DBC-E019] %s: Failed to run SQLPlus (%s)"
    E020 = "[DBC-E020] Zipfile already exists (try --overwrite): %s"
    E021 = "[DBC-E021] No AWR or Statspack detected for %s (try --force-awr or --ignore)"
    E022 = "[DBC-E022] Worker failed, rc=%s"
    E023 = "[DBC-E023] Job generator failed, rc=%s"
    E024 = "[DBC-E024] NMON directory not found: %s"
    E025 = "[DBC-E025] Not a valid NMON file: %s"
    E026 = "[DBC-E026] %s: Parsing instance info failed"
    E027 = "[DBC-E027] %s: No valid connection (check credentials?)"
    E028 = "[DBC-E028] Cannot obtain oracle base directory (%s)"
    E029 = "[DBC-E029] %s: No credentials provided"
    E030 = "[DBC-E030] %s: (%s) Timeout connecting to instance"
    E031 = "[DBC-E031] %s: No valid ORACLE_HOME provided (try --orahome)"
    E032 = "[DBC-E032] Cannot read credentials file %s"
    E033 = "[DBC-E033] %s: Instance not available (%s:%s)"
    E034 = "[DBC-E034] %s: Invalid credentials provided (%s:%s)"
    E035 = "[DBC-E035] %s: Unknown Oracle error, see logfile (%s:%s)"
    E036 = "[DBC-E036] %s: TNS connection issue (%s:%s)"
    E037 = "[DBC-E037] %s: Insufficient privileges [%s:%s]"
    E038 = "[DBC-E038] %s: Insufficient privileges on V$ tables [%s:%s]"
    E039 = "[DBC-E039] %s: Incomplete set of workload reports (failed workers)"
    E040 = "[DBC-E040] %s: [%s] Cannot execute AWR generation procedure [%s:%s]"
    E041 = "[DBC-E041] %s: SQLPlus query failed, returncode=%s (see logfile)"
    E042 = "[DBC-E042] %s: No valid ORACLE_HOME found (see logfile)"
    E043 = "[DBC-E043] Bad connectstring format: %s"
    E044 = "[DBC-E044] Command not found in $PATH: %s"
    E045 = "[DBC-E045] Timeout on sending root tasks (Queue Full)"
    E046 = "[DBC-E046] Timeout on receiving root tasks (Queue Empty)"
    E047 = "[DBC-E047] Timeout on waiting for collector, cannot send root tasks"

class ErrorHelp():
    @classmethod
    def help(cls, err):
        err = err.replace('DBC-','').upper()
        try:
            helpmsg = getattr(Errors, err)
            helptxt = getattr(ErrorHelp, err)
            print(helptxt)

        except AttributeError:
            print('No help message available for error {0}'.format(err))

    W001 =  "A subprocess was aborted due to a keyboard interrupt (CTRL-C).\n\n" \
            "Solution:\n\nIf dbcollect was aborted, restart it with the correct parameters."
    W002 =  "Informational message: DBCollect could not find prior usage of AWR reports, but the force flag was used so it continues genertating AWR reports anyway.\n\n" \
            "Solution:\n\nNo action required, DBcollect will proceed normally."
    W003 =  "Saving some data in the DBCollect ZIPfile failed due to (message).\n\n" \
            "Solution:\n\nNo action required, DBcollect will proceed normally."
    W004 =  "DBCollect could not detect prior AWR usage on <instance> and skips AWR reports alltogether for this instance due to the ignore flag.\n\n" \
            "Solution:\n\nNo action required, DBcollect will proceed normally. Be informed that the DBCollect data will be incomplete and may not result in the correct assessment."
    W005 =  "The given command failed to execute. Possible reasons:\n\n" \
            "- The command does not exist in $PATH\n" \
            "- Command requires root privileges (dbcollect never runs as root)\n\n" \
            "Solution:\n\nNo action required, DBcollect will proceed normally, just skipping the problematic command"
    W006 =  "On Linux, DBCollect tries to retrieve platform information via virtual files (/sys/class/dmi/id). Some of these files cause OS errors when trying to read them.\n\n" \
            "Solution:\n\nNo action required, DBcollect will proceed normally."
    W007 =  "A detected instance is not processed because a credentials file is used and the \"enabled\" field in the credentials file is set to \"N\".\n\n" \
            "This is needed to avoid trying to connect to a MOUNTED (Standby DB instance) or STARTED instance, resulting in all kinds of errors."
    W008 =  "The sysstat RPM package is not installed. Sysstat is used to retrieve OS performance statistics (/var/log/sa?? files)\n\n" \
            "Solution:\n\nInstall (and enable where needed) the sysstat package using\n\ndnf install sysstat\nsystemctl enable --now sysstat\n"
    W009 =  "The sysstat timer is not enabled. Sysstat is used to retrieve OS performance statistics.\n\n" \
            "Solution: Enable the sysstat timer, using\n\nsystemctl enable --now sysstat-collect.timer\n"
    W010 =  "The ORACLE_HOME/rdbms/lib/config.c file cannot be parsed. This file is used to check if the user is in the correct dba group.\n" \
            "Check permissions and contents of this file."
    W011 =  "The user is not a member of the correct DBA group (as detected from rdbms/lib/config.c).\n\n" \
            "Add the user to the group (gpasswd -a <user> <group>), login again and retry.\n\n" \
            "Alternatively, when using multiple oracle users, create another (temporary) DBA user who is member of all required DBA groups\n\n"
    W012 =  "Result of ORA-01017. This is usually caused by the user not being a member of the correct DBA group. See W011 for more details\n\n"
    W013 =  "This instance was excluded using the --excluded parameter\n\n"
    W014 =  "This instance was not include using the --included parameter. When using --included, only the listed instances will be processed.\n\n"
    W015 =  "No instance detection will be used, so dbcollect will skip any running instance that is not in the logons file."
    W016 =  "SQL*Plus returned an error when trying to connect. The next ORACLE_HOME will be attempted if available."
    W017 =  "This usually happens if the database is down (when using logins), or in the process of starting or shutting down, or when using the incorrect ORACLE_HOME."

    E001 =  "This indicates an unexpected error in DBCollect due to a bug.\nSolution: Unknown, submit the logfile for debugging."
    E002 =  "DBCollect has been aborted, usually due to CTRL-C (cancel) keyboard sequence.\nSolution: restart dbcollect with the correct parameters."
    E003 =  "This happens if DBcollect cannot create the ZIP file for whatever reason.\nSolution: Try to find out why the ZIP file cannot be created (permissions?, Filesystem /tmp full?), try another location"
    E004 =  "This happens if DBcollect cannot read a file as part of the collected data.\nA common cause is when the file is a virtual file which cannot be read by the OS.\nSolution:\n\n" \
            "It is not a critical problem, DBCollect will proceed with the rest of the tasks.\n\nSolution 2:\n\ndbcollect runs as non-root (see Security) and cannot read the SAR files." \
            "If the file is a SAR file: /var/log/sa/saXX, you can provide read access to others for these files:\nchmod o+r /var/log/sa/sa*"
    E005 =  "This happens if DBcollect cannot read a file as part of the collected data.\nIt is related to error E004 depending on the Python version.\n\n" \
            "Solution:\n\nSome systems have non-standard security policies, preventing dbcollect to read these files. It may be undesirable to change the permissions with chmod." \
            "In these cases you can use file access control lists to set an ACL permission without changing the basic permissions. The command is (example)\n\n" \
            "setfacl -m u:oracle:r /var/log/sa assuming the database user under which dbcollect runs is oracle.\nIf these files are 'pseudo' files" \
            "(such as in /sys, /proc etc) the permissions will be reset to normal at the first reboot. "
    E006 =  "DBCollect tried to strip the HTML (AWR) file from SQL sections, but encountered a HTML format error in the file (possibly the AWR report itself is corrupt or invalid).\n\n" \
            "Solution:\n\nThe AWR files are stored without stripped SQL code. You may not want this. Inspect the ZIP file to make sure.\n" \
            "It is also possible that the AWR file(s) are corrupted or not created correctly (invalid HTML but no AWR report at all). If this happens with one or a few files, it is safe to ignore. If it happens with lots of files, report the error. "
    E007 =  "DBCollect could not write a temporary HTML file after running AWR Strip.\n\nSolution:\n\nMaybe the temp directory is (almost) full." \
            "Try cleaning up space, use a different temp dir (--tempdir) or find out why otherwise the files cannot be written.\n" \
            "Also make sure that the user dbcollect uses has access to the temp directory (this is not the root user!)\n" \
            "Check the logfile to see which user was used, for example:\n\n2024-10-10 04:00:26:INFO  : Current user is oracle"
    E008 =  "The OS on which DBCollect is executing is not supported.\n\nSolution: Check if the platform you run on is supported. If you think it is, file a bug report."
    E009 =  "Running an SQL*Plus script resulted in an error. DBCollect will continue.\n\nSolution:\n\nContinue processing with the missing report, or file a bug report"
    E010 =  "Running an SQL*Plus script resulted in a timeout. DBCollect will continue.\n\nSolution:" \
            "This is most likely caused by known Oracle issues with the Recyclebin and/or DBA_FREE_SPACE.\nIf this happens when running AWR reports, see https://wiki.dirty-cache.com/AWR_Performance \nTBD... "
    E011 =  "The job generator timed out due to extremely slow generation of AWR reports.\n\nSee https://wiki.dirty-cache.com/AWR_Performance for possible solutions."
    E012 =  "An I/O error happened reading/writing to <file> caused DBCollect to abort.\n\nSolution:\n\n" \
            "If the I/O error is \"Permission Denied\", see if it can be fixed with chmod on the file or directory. Otherwise, submit a bug report."
    E013 =  "An unexpected error caused a worker subprocess to abort.\n\nSolution: This is a bug. Please submit a bugreport."
    E014 =  "Creating the DBCollect logfile (/tmp/dbcollect.log) failed.\n\nSolution:\n\n" \
            "Check if the /tmp directory has free space. It could also be that a dbcollect.log file exists from another dbcollect run with a different user. Remove the logfile and retry."
    E015 =  "DBCollect failed to read <file> as part of the set of OS files to be collected, due to an unexpected error (not a known I/O error - these are handled normally)\n\n" \
            "Solution: Ignore this error and proceed."
    E016 =  "DBCollect failed to find or read oraInst.loc. This file is required to get a list of ORACLE_HOME directories.\n\n" \
            "Solution:\n\nCheck if the file /etc/oraInst.loc exists. If it is not there, Oracle is probably not properly installed.\n\n" \
            "Solution 2:\n\nManually provide an ORACLE_HOME using the --orahome option\n\nFurther info:\n\n" \
            "The oraInst.loc contains information on where the Oracle Inventory resides. If this information is not there, dbcollect cannot find the Oracle Inventory."
    E017 =  "DBCollect failed to find or read inventory.xml. This file is required to get a list of ORACLE_HOME directories.\n\n" \
            "Solution:\n\nThe file /etc/oraInst.loc points to the location of the Oracle Inventory. In the inventory there should be a file named inventory.xml.\n\n" \
            "Example: /u01/app/oraInventory/ContentsXML/inventory.xml\n\n" \
            "If this information is not there, dbcollect cannot detect ORACLE_HOME directories.\n\n" \
            "Solution 2:\n\nManually provide an ORACLE_HOME using the --orahome option"
    E018 =  "DBCollect failed to find or read oratab. This file is required to get a list of ORACLE_HOME directories.\n\n" \
            "Solution: Check if either /etc/oratab (linux, AIX) or /var/opt/oracle/oratab (SunOS) exists and is readable to the oracle user.\n\n" \
            "If this seems to be ok, please submit a bugreport."
    E019 =  "DBCollect tried to run SQL*Plus but failed due an OS error (see <message>)\n\nSolution:\n\n" \
            "Check if you can manually start SQLPlus from the same $ORACLE_HOME using the full path from the error message.\n\n" \
            "If this all works, please submit a bugreport"
    E020 =  "DBCollect tried to create a new zipfile but the file already exists.\n\n" \
            "Solution: Run dbcollect with --overwrite or -o to overwrite the existing zipfile.\n\n" \
            "Note: The /tmp/dbcollect-*.zip file contains no critical data and can be safely overwritten"
    E021 =  "DBCollect could not detect prior AWR usage and no statspack configuration for this instance.\n\nSolution:\n\n" \
            "(Only if you have Diagnostics Pack license for the host!): Run dbcollect with --force-awr\n\n" \
            "Solution 2:\n\nSetup Statspack, wait for at least a week to generate data and rerun (if you do not have the Diagnostics license)\n\n" \
            "Solution 3:\n\nRun dbcollect with --ignore to skip performance data for all databases completely. Beware that this may lead to incomplete workload assessment results."
    E022 =  "A worker subprocess failed with the given returncode.\n\nSolution:\n\n" \
            "Check the logfiles for any issues. If the problem remains, please submit a bugreport"
    E023 =  "The job generator subprocess failed with the given returncode.\n\nSolution:\n\n" \
            "Check the logfiles for any issues. If the problem remains, please submit a bugreport"
    E024 =  "The NMON directory specified with --nmon <dir> could not be found\n\nSolution:\n\n" \
            "Specify the correct NMON directory and make sure it contains valid NMON files (each NMON file starts with \"AAA,progname\")"
    E025 =  "The file listed is not a valid NMON file.\n\nSolution:\n\nUnknown, submit the logfile for debugging."
    E026 =  "Retrieving metadata for instance <sid> failed.\n\nSolution:\n\nUnknown, submit the logfile for debugging."
    E027 =  "dbcollect could not make a valid connection to Oracle instance <sid>.\n\nSolution:\n\n" \
            "Try again with different credentials (if using a credentials file) or specify an alternative ORACLE_HOME using --orahome "
    E028 =  "The orabasetab file cannot be opened.\n\nSolution:\n\nCheck the existence, permissions and contents on this file.\n\n" \
            "It should be located in $ORACLE_HOME/install/orabasetab"
    E029 =  "A running Oracle instance has been detected, a credentials file is specified but it has no entry for the given instance.\n\n" \
            "Solution:\n\nAdd an entry to the credentials file"
    E030 =  "dbcollect could not connect with the instance <sid> within the given timeout (currently 2 seconds).\n\n" \
            "Solution: Figure out why connecting using SQL*Plus takes so long"
    E031 =  "A running Oracle instance has been detected, but no ORACLE_HOME is detected to use with the instance.\n\n" \
            "Potential cause: No entry in /etc/oratab or the permissions do not allow the user to read this file.\n\n" \
            "Solution:\n\nVerify contents and permissions of the oratab file."
    E032 =  "A running Oracle instance has been detected, a credentials file is specified but it cannot be read by dbcollect\n\n" \
            "Solution:\n\nCheck permissions of the credentials file. The user dbcollect runs as, may not have access."
    E033 =  "The instance <sid> is not in OPEN mode, so dbcollect cannot connect to it using TNS connection string. The instance may be in MOUNTED mode (Standby database) or in STARTED mode.\n\n" \
            "Solution:\n\nSkip the instance using an N in the 2nd field of the credentials file.\n\n" \
            "Solution 2:\n\nOpen the database (if it should be opened)\n\n" \
            "Solution 3: \n\nRun dbcollect as oracle (or root) user without credentials file (in which case it connects as SYSDBA without requiring a TNS connection"
    E034 =  "Invalid username/password provided in the credentials file for the given instance\n\nSolution:\n\nUpdate the entry to the credentials file"
    E035 =  "An unknown SQL*Plus error occured - the dbcollect.log file should show the full output of the error message\n\n" \
            "Solution:\n\nUnknown, please provide the contents of the logfile"
    E036 =  "An SQL*Plus error occured related to TNS networking - the dbcollect.log file should show the full output of the error message\n\n" \
            "Solution:\n\nDiagnose the connection problem (try manually connecting using SQL*Plus and the given connect url from the credentials file)"
    E037 =  "The connection to instance <sid> failed because the user has no CREATE SESSION privileges\n\n" \
            "Solution:\n\nGrant CREATE SESSION to the user listed in the credentials file"
    E038 =  "The connection to instance <sid> failed because the user has no privileges to read V$ or DBA_* tables.\n\n" \
            "Solution:\n\nGrant SELECT ANY DICTIONARY to the user listed in the credentials file"
    E039 =  "Some worker processes failed (either due to timeouts or due to AWR generation issues.\n\n" \
            "Solution:\n\nIf there are timeout messages, diagnose AWR timeouts. For other errors, please provide the logfile."
    E040 =  "Creating AWR reports failed with the given Oracle message. More debug info should be in the dbcollect.log file.\n\n" \
            "The most likely cause is not having EXECUTE privileges on the DBMS_WORKLOAD_REPOSITORY procedures.\n\n" \
            "Solution:\n\nGRANT EXECUTE ON DBMS_WORKLOAD_REPOSITORY to <user>"
    E041 =  "An SQL query used to retrieve metadata failed for some reason (logfile dbcollect.log should show more details)\n\n" \
            "This query usually involves meta.sql, getawrs.sql or getsps.sql.\n\n" \
            "Solution:\n\nDiagnose the error or send the output of the logfile."
    E042 =  "No valid ORACLE_HOME was found from all provided ORACLE_HOMES.\n\n" \
            "Check user permissions and ORACLE_HOME configuration"
    E043 =  "The connectstring file for the --connect option must have valid Oracle connectstrings on each line.\n\n" \
            "Commented lines start with '#'.\n\n" \
            "The format for each line should be <user>/<password>//<hostname or fqdn>/<service>. For example: \n\n" \
            "dbsnmp/secret1234@//example.com/orcl\n\n"
    E044 =  "The listed command is not found in $PATH (/usr/sbin:/usr/bin:/bin:/sbin).\n\n"
    E045 =  "The process that runs tasks as root could not send the task results to the receiver. This should not happen and indicates a bug or other problem"
    E046 =  "No more task results could be received but the sender did not complete successfully. Can be a side effect of a long running (root) process."

