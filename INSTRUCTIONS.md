# Installation

## Notes

_dbcollect_ is a tool written in Python and distributed as a Python "ZipApp" package. The only thing you need to do to install it, is put it somewhere in the PATH and make it executable.

## Easy way

Assuming the prerequisites are met, the easiest way to install the latest version of _dbcollect_ is to run the downloader command on your host and move it to $PATH:

```
# This requires internet access via https
# Root install
curl -L https://github.com/bsjerps/dbcollect/releases/latest/download/dbcollect -o /usr/local/bin/dbcollect && chmod 755 /usr/local/bin/dbcollect

# User install
curl -L https://github.com/bsjerps/dbcollect/releases/latest/download/dbcollect -o $HOME/bin/dbcollect && chmod 755 $HOME/bin/dbcollect
```

## Prerequisites

* Python 2.6 or higher, or 3.6 or higher
* Python-argparse (is usually included in the Python distribution except for very old versions)
* Enterprise Linux 6, 7, 8 or 9, Solaris 11, IBM AIX 7
* Some free space in /tmp (or elsewhere, use --tempdir)

For Oracle (dbcollect will just pick up OS files if no Oracle databases are detected):

* Oracle RDBMS 11g or higher (optional)
* Diagnostics pack license OR statspack configured on the database(s)
* Access to the 'oracle' special user or dba privileges ('root' not required) or a credentials file
* Database instances up and running (opened read/write required for AWR/Statspack)

### Linux

On Enterprise Linux 7 (RHEL 7, OEL 7, CentOS 7), Python2 is installed by default including the argparse module.

Enterprise Linux 8 (RHEL 8, OEL 8) should now work fine as dbcollect is Python3 compatible. 'python' may not be configured by default, you can set 'python' to use python3:

```alternatives --set python /usr/bin/python3```

Older Linux versions (RHEL5) do not work unless there is a more recent version of Python on the system.

### AIX

On IBM AIX, you need to install Python first. You can get python for AIX from
[AIX Toolbox (IBM)](https://www.ibm.com/support/pages/aix-toolbox-linux-applications-overview)

You may need to run using python:
```python3 /usr/local/bin/dbcollect <options>```


### SPARC/Solaris

On Solaris, Python should be already available. It may be an older version.

You may need to run using python:

`python3 /usr/local/bin/dbcollect <options>`

### HP-UX

HP-UX has experimental support.
You may need to run using python:

`python3 /usr/local/bin/dbcollect <options>`

### Windows

_dbcollect_ does not yet support Windows. Let me know if you need it.

### Manual install

You can download or inspect the installer first if needed. If you prefer to manually download _dbcollect_, download it from this link:

[latest version](https://github.com/bsjerps/dbcollect/releases/latest/download/dbcollect)

[other versions](https://github.com/bsjerps/dbcollect/releases)

Place _dbcollect_ in /usr/local/bin (root) or $HOME/bin (oracle or dba user) and make it executable:

`chmod 755 /usr/local/bin/dbcollect`

(alternatively you can run it via `python /usr/local/bin/dbcollect`)

### Updating

```
# Update dbcollect:
dbcollect --update
# Without root access, the new version will be saved as /tmp/dbcollect.
# Move it manually to the required location.
```

# Usage

## Basic operation

In the majority of cases, simply run _dbcollect_ and it will run with default options. About 10 days of AWR reports will be created for each detected running Oracle instance (depending on AWR retention). SAR data is usually picked up for 30/31 days (1 month) where available.

## Diagnostics Pack license

Creating AWR reports requires Oracle Diagnostic Pack license. _dbcollect_ tries to detect prior usage of AWR and if this is detected, AWR reports are generated. If prior AWR usage is **not** detected, _dbcollect_ will abort with an error. If you have Diagnostic Pack license but not created AWR reports, you can force _dbcollect_ to generate AWR reports using the `--force-awr` flag (see below).

## Oracle RAC

By default, _dbcollect_ picks up AWR reports from **ALL** RAC instances. This means if you run _dbcollect_ on multiple RAC nodes, most of the AWR reports will be created multiple times. To avoid this, use the `--no-rac` option (see below). This will significantly reduce the time it takes to run _dbcollect_ and the size of the generated ZIP file.

Only use this if you run _dbcollect_ on **all** RAC nodes.

## Transferring DBCollect ZIP files

When complete, a ZIP file will be created in the /tmp directory. This file contains the database overview and, by default, the last 10 days of AWR or Statspack reports. All temp files will be either cleaned up or moved into the ZIP archive. It also contains the dbcollect.log file that can be used for troubleshooting in case something went wrong.

You can inspect the ZIP file using normal zip/unzip tools (if installed):

```
# List the contents of the ZIP file
unzip -v /tmp/dbcollect-hostname.zip

# Dump contents of a file on stdout (avoid binary files, they create a mess):
unzip -qc /tmp/dbcollect-hostname.zip hostname/dbcollect.log
```


The ZIP file can be sent to the author in several ways, but make sure the original dbcollect-*.zip files are **UNMODIFIED**!

This means, do not unpack and re-pack the file(s) as this causes problems with the file metadata. If you want to encrypt the files, use a container archive (ZIP, TAR, 7-zip or whatever) and pack the original, unmodified dbcollect files in the new archive.

The files can be uploaded to a NextCloud dropbox: [DBCollect Dropbox](https://cloud.sjerps.eu/s/dbcollect)
Also, if a project has been setup already on LoadMaster (the reporting engine), the owner of the project can generate a unique URL for uploading directly onto the engine, using a URL like `https://loadmaster.dirty-cache.com/dropbox?uuid=<unique_uuid>`

Both of these methods are HTTPS encrypted.

## Command line options

```
# Run with default options (run as root or oracle user)
dbcollect

# List available options (help)
dbcollect -h

# Version info
dbcollect -V

# Debug (prints many debug messages, dumps the dbcollect.log after finishing)
dbcollect --debug

# Quiet (only print error messages)
dbcollect --quiet

# Update to latest version (requires https)
dbcollect --update

# Non-standard Oracle user (only needed if running as root)
dbcollect --user sap

# Write ZIP file with different filename (will go to /tmp)
dbcollect --filename mydbcollect.zip

# Write ZIP file to other directory than /tmp
dbcollect --filename /home/oracle/mydbcollect.zip

# Use alternative temp directory
dbcollect --tempdir /var/tmp

# Collect more than 10 days of AWR data (if available)
dbcollect --days 31

# Shift collect period so you pick up from 30 days ago to 10 days ago
dbcollect --days 30 --end_days 10

# Use logons file instead of connect using OPS$
# This allows dbcollect to run as non-privileged user (i.e., 'nobody'), and a read-only
# Oracle user (i.e., DBSNMP). See "using a logons file" below
dbcollect --logons /tmp/logons.txt

# Specify the ORACLE_HOME
# Use if the OS user has no access to oratab/oracle inventory
dbcollect --orahome /u01/app/oracle/product/21.0.0/dbhome_1

# Force using AWR even if license is not detected:
dbcollect --force-awr
# note this also picks up AWRs that have been generated with init.ora setting control_management_pack_access=NONE

# Use statspack even if AWR usage is detected
dbcollect --statspack

# Don't create AWR reports for databases without previous AWR usage
# Only use as last resort!
dbcollect --ignore-awr

# Remove all SQL code from AWR reports (not for statspack)
dbcollect --strip

# Pick up local AWRS only (Oracle RAC) - if you plan to run dbcollect on ALL RAC nodes
dbcollect --no-rac

# Do not pick up AWRs from Data Guard Standby databases
dbcollect --no-stby

# Don't create AWR reports at all (only the dbinfo sql reports)
dbcollect --no-awr

# Don't pick up SAR reports
dbcollect --no-sar

# Don't run any Oracle specific tasks
dbcollect --no-ora

# Don't run any OS specific tasks (only the Oracle stuff)
dbcollect --no-sys

# Don't run root tasks (even if executed as root)
dbcollect --no-root

# Don't pick up process accounting even if available
dbcollect --no-acct

# Ignore problematic Oracle inventory
dbcollect --no-orainv

# Ignore problematic oratab
dbcollect --no-oratab

# Ignore timeout when detecting instancs:
dbcollect --no-timeout

# Pick up NMON files from directory
dbcollect --nmon /var/nmon_dir

# Skip problematic/hanging SQL scripts
dbcollect --skip-sql pdb_tempspace.sql,another.sql

# Skip problematic/hanging OS commands
dbcollect --skip-cmd lshw,dmidecode

# Only include a subset of databases (ignore all others)
dbcollect --include probdb1,probdb3

# Exclude one or more problem databases
dbcollect --exclude probdb1,probdb3

# Limit amount of concurrent AWR collection tasks (CPUs)
dbcollect --tasks 2

# Set timeout (in minutes) on AWR generation (default 10 minutes)
dbcollect --timeout 30

# Speed up AWR generation (higher CPU consumption)
# (sets tasks to number of CPUs)
dbcollect --tasks 0

# Show details on an error message
dbcollect --error E001

```

## Using a logons file

With the option ```--logons <logons file>```, _dbcollect_ will make SQL\*Plus connections using SQL\*Net with any database user, instead of OS (OPS$) connections using SYSDBA privileges.

This allows _dbcollect_ to run as any OS user (i.e., 'nobody'), because it no longer requires OS level authentication, as long as it has access to a valid Oracle SQL*Plus environment (ORACLE_HOME).

* OS user must have access to a valid ORACLE_HOME for running SQL\*Plus.
* A credentials file must be provided with a (readable) file containing a valid connect url for each instance.
* The privileges must be provided in the logons file where each line has the form ```user/password@hostname/instance```.
* The database user must have read access to v$, DBA_\* and CDB_\* tables (provided by the ```SELECT ANY DICTIONARY``` privilege)
* This requires the listener to be available and listening for the provided service.

The ```DBSNMP``` user is predefined with these privileges. When using ```DBSNMP``` for this purpose, it must be unlocked and have a valid password on each instance.

The ```ORACLE_HOME``` will be retrieved from ```/etc/oratab``` but can be provided with ```--orahome``` if oratab is not valid or available for the OS user.

The database user/password must be provided in the logon definition as such:

`user/password@hostname/instance`

For example:
```
dbsnmp/topsecret@//example.local/orcl
johndoe/topsecret@//test.local/orcl2
```

Note that _dbcollect_ will try to connect to each enabled and running instance, and will fail if any of the provided credentials are invalid or missing, or the connection cannot be made for whatever reason. There is a 10 second timeout for hanging connections.

The OS user does not even need to have a valid OS login, it can be executed as root using the ```runuser``` command:

```
echo '/usr/local/bin/dbcollect --logons /tmp/logons' | runuser nobody -s /bin/bash
# or (cleaner)
runuser nobody -s /bin/bash <<< "/usr/local/bin/dbcollect --logons /tmp/logons.txt <options>"

```
An example wrapper script is provided in the [contrib](https://github.com/bsjerps/dbcollect/tree/master/scripts) directory.


### More info

The dbcollect ZipApp package contains everything such as Python files and SQL scripts in a single file.

It is a standard ZIP file - only prepended with a Python "shebang":

```#!/usr/bin/env python```

For inspection you can unzip the package using a standard ZIP tool. It is not recommended to run _dbcollect_ in any other way than via the distributed package. Although it works, avoid using `git clone` or other ways to run it from the github sources.


