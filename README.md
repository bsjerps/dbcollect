DBCollect - Oracle Database Info Collector
======================

![logo](https://github.com/bsjerps/dbcollect/blob/master/artwork/dbcollect-logo.png)


## Online manuals

Detailed manuals for _dbcollect_ are available here:
- [DBCollect Manuals](https://dbcollect.dirty-cache.com)
- [Quickstart](https://dbcollect.dirty-cache.com/quickstart/)

## Description

_dbcollect_ is a metadata collection tool for Oracle databases, providing workload and config data from database hosts for:

- LoadMaster (The advanced DB workload analyzer tool I have developed - more info TBD)
- Dell LiveOptics (Oracle feature now obsolete)
- Dell internal database sizing tool (obsolete)

It is written in Python, and collects various OS configuration files and
the output of some system commands, as well as AWR or Statspack reports for each
database instance, and other database information.

The results are collected in a ZIP file named (default):
`/tmp/dbcollect-<hostname>-<timestamp>.zip`

For the advanced analyzer (LoadMaster), send the entire ZIP file (via secure FTP or other means).

## Collected data

- Host system configuration (CPU type, memory, storage, ...)
- Host performance data (SAR/Sysstat or NMON)
- Oracle configuration for each instance (various details from system tables)
- Oracle AWR reports (for a default period of 10 days for each instance) or (alternatively) Statspack

## License

*dbcollect* is licensed under GPLv3. See `COPYING` for more info or go to [GPLv3+ License Info](https://www.gnu.org/licenses/gpl-3.0.html)

## Author

Bart Sjerps (bart &lt;at&gt; dirty-cache &lt;dot&gt; com) - with great contributions from others
