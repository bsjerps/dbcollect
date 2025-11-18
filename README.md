DBCollect - Oracle Database Info Collector
======================

![logo](https://github.com/bsjerps/dbcollect/blob/master/artwork/dbcollect-logo.png)


## Wiki Manuals

Detailed manuals for _dbcollect_ are available here: [Dirty Cache Wiki - DBCollect/Manuals](https://wiki.dirty-cache.com/DBCollect/Manuals)


## Description

_dbcollect_ is a metadata collection tool for Oracle databases, providing workload and config data from database hosts for:

* LoadMaster (The advanced DB workload analyzer tool I have developed - more info TBD)

It is written in Python, and collects various OS configuration files and
the output of some system commands, as well as AWR or Statspack reports for each
database instance, and other database information.

The results are collected in a ZIP file named (default):
`/tmp/dbcollect-<hostname>.zip`

For LiveOptics and Dell's Workload Analyzer, the per-database directories in the ZIP file contain all files you need to upload to the reporting tools.

For the advanced analyzer (LoadMaster), send the entire ZIP file (via secure FTP or other means).

## Installation

### Linux, as root

This sets up dbcollect in /usr/local/bin for all users.

```
# Setup dbcollect
curl -L https://github.com/bsjerps/dbcollect/releases/latest/download/dbcollect -o /usr/local/bin/dbcollect && chmod 755 /usr/local/bin/dbcollect

# Test functionality
dbcollect -V

# If you get Python errors
alternatives --set python /usr/bin/python3
```

### Linux, as non-root (i.e. DBA user)
```
# Setup user bin directory if it does not already exist
mkdir -p $HOME/bin

# Setup DBCollect
curl -L https://github.com/bsjerps/dbcollect/releases/latest/download/dbcollect -o $HOME/bin/dbcollect && chmod 755 $HOME/bin/dbcollect

# Test functionality
dbcollect -V

# If you get Python errors
python3 ~/bin/dbcollect -V
```

### Manual install

* Download latest dbcollect: [latest dbcollect version](https://github.com/bsjerps/dbcollect/releases/latest/download/dbcollect)
* Move it to ```/usr/local/bin``` (if you are root) or ```$HOME/bin``` (if you are not root)
* Make it executable: ```chmod 755 /usr/local/bin/dbcollect```
* Test if it works (run with help option): ```dbcollect -V```
* Collect the data: ```dbcollect```
* Get and upload the dbcollect ZIP datafile (```/tmp/dbcollect-<hostname>.zip```)

## Info collected by dbcollect:

- AWR or Statspack reports for a default period of about 10 days
- Database configuration (such as version, dbname, database and system settings)
- Database file info (sizes and settings of datafiles, tempfiles, redo logs, control files etc)
- Additional database file info (backup, archive logs, flashback logs)
- Tablespace details, Segment sizes, AWR/Statspack details
- ASM disk group and disk info
- Init parameters
- Feature usage
- Linux: CPU, memory, disks, network interfaces etc
- AIX, Solaris (SPARC): CPU, memory, limited other info
- SAR: Binary SAR files (Linux) or SAR reports (UNIX) (Linux SAR provides much more detail)
- Process accounting summaries (Linux only)
- HP/UX: Experimental support
- Windows: Not yet supported (TBD)

More collectors may be added in the future.

### Important note

Ideally, _dbcollect_ collects Oracle AWR reports in HTML format as HTML can be processed (parsed) reliably.
It can also generate Statspack reports. This is how _dbcollect_ decides which reports to produce:

Oracle AWR reports require Diagnostics Pack (see Oracle doc id 1490798.1).
_dbcollect_ can not directly determine if you have this license or not - it checks the dba_feature_usage_statistics
table whether "AWR Reports" has been used previously or not, and falls back to Statspack otherwise, unless the ```--force-awr``` flag
has been specified. The decision flow is as follows:

1. Check if 'AWR Reports' is a feature that has been used before. If so, use AWR reports
2. If AWR usage is not detected but the ```--force-awr``` flag has been specified, use AWR reports
3. If AWR usage is not detected and no ```--force-awr``` flag is specified, check if STATSPACK is available. If so, use Statspack
4. If AWR usage is not detected, no ```--force-awr``` has been specified and no statspack reports are available, but ```--ignore``` is specified, ignore and continue to the next
5. If AWR usage is not detected, no ```--force-awr``` has been specified and no statspack reports are available, abort with an error

So if you ARE licensed for Diagnostics Pack but _dbcollect_ complains, you can run dbcollect with the --force-awr option.
DBcollect will only warn about the AWR detection and just generate the reports anyway.

** Use the `--force-awr` flag ONLY if you are sure you are correctly licensed! **

If you are NOT licensed for diagnostics pack then you can use Statspack instead (see section below)

More info on Oracle feature usage: [Oracle Feature Usage](https://oracle-base.com/articles/misc/tracking-database-feature-usage)

### Non-Linux (UNIX) systems

DBCollect now supports AIX and Solaris systems, and HP-UX has experimental support. You need to have Python installed (at least version 2.6).

Running _dbcollect_ directly may not work, then run it with ```python3 /usr/local/bin <options>```

Windows is not (yet) supported.

## Requirements

See [Dirty Cache Wiki - DBCollect/Install](https://wiki.dirty-cache.com/DBCollect/Install) for more details.

## Known limitations and caveats

- Backup files, logs etc may no longer exist but still be reported, depending on backup catalog accuracy. Best effort.
- Very long names for files, tablespaces, disk groups etc may be truncated/wrapped
- Very large sized elements or very large amounts of objects may result in `####` notation and no longer be useful. Limits have been increased to insane values so this should not be a problem
- Newer Oracle versions (23 and up) may cause unreliable numbers, not yet tested
- Oracle RAC sometimes is very slow with generating AWR reports. Known issue. Be patient. See [Dirty Cache Wiki - DBCollect Troubleshooting](https://wiki.dirty-cache.com/DBCollect/Troubleshooting)

## Safety

A lot of safety guards have been built into _dbcollect_. It is designed to not require root access and only writes files to the /tmp directory by default. Even if it fails for some reason, no harm can be done.

More info can be found in [Dirty Cache Wiki - DBCollect Security](https://wiki.dirty-cache.com/DBCollect/Security)

## Source code

dbcollect is packaged as a Python "zipapp" package which is a specially prepared ZIP file. You can unzip it with a normal unzip tool.
For example, listing the files in the package:

`unzip -l /usr/local/bin/dbcollect`

## Q&A

See [Dirty Cache Wiki - DBCollect FAQ](https://wiki.dirty-cache.com/DBCollect/FAQ)

## License

_dbcollect_ is licensed under GPLv3. See "COPYING" for more info or go to [GPLv3+ License Info](https://www.gnu.org/licenses/gpl-3.0.html)

## Author

Bart Sjerps (bart &lt;at&gt; dirty-cache &lt;dot&gt; com) - with great contributions from others
