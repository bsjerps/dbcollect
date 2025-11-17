-----------------------------------------------------------------------------
-- Title       : unlock_dbsnmp.sql
-- Description : Unlock Oracle read-only user (dbsnmp)
-- Author      : Bart Sjerps <bart@dirty-cache.com>
-- License     : GPLv3+
-----------------------------------------------------------------------------

accept PASSWD prompt 'Enter password for DBSNMP: '

ALTER USER dbsnmp ACCOUNT UNLOCK;
ALTER USER dbsnmp IDENTIFIED BY &PASSWD;
