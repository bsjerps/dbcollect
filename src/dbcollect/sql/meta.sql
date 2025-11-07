-----------------------------------------------------------------------------
-- Title       : meta.sql
-- Description : Get Oracle instance and database metadata in JSON format
-- Author      : Bart Sjerps <bart@dirty-cache.com>
-- License     : GPLv3+
-----------------------------------------------------------------------------

SET SERVEROUTPUT ON
SET tab off feedback off verify off heading on lines 9999 pages 50000 trims on

ALTER SESSION SET nls_date_format='YYYY-MM-DD HH24:MI:SS';
WHENEVER SQLERROR EXIT 0

DECLARE
	v_status    VARCHAR(100);
	v_version   INTEGER;
	v_instance  VARCHAR(1000);
	v_database  VARCHAR(1000);
	v_feat      VARCHAR(1000);
	v_osstats   VARCHAR(100);
	v_awr       INTEGER;
	v_statspack INTEGER;
BEGIN
	SELECT status INTO v_status FROM v$instance;
	SELECT regexp_substr(version, '\d+') INTO v_version FROM v$instance;

	SELECT            '  "instance_number": ' || instance_number || ', '
		|| chr(10) || '  "instance_name": '   || chr(34) || instance_name   || chr(34) || ','
		|| chr(10) || '  "host_name": '       || chr(34) || host_name       || chr(34) || ','
		|| chr(10) || '  "version": '         || chr(34) || version         || chr(34) || ','
		|| chr(10) || '  "startup_time": '    || chr(34) || startup_time    || chr(34) || ','
		|| chr(10) || '  "status": '          || chr(34) || status          || chr(34) || ','
		|| chr(10) || '  "parallel": '        || chr(34) || parallel        || chr(34) || ','
		|| chr(10) || '  "sysdate": '         || chr(34) || sysdate         || chr(34) || ','
		|| chr(10) || '  "dbuser": '          || chr(34) || user            || chr(34) || ','
		|| chr(10) || '  "version_major": '   || v_version
	INTO v_instance FROM v$instance;

	IF v_status IN ('MOUNTED', 'OPEN') THEN
		SELECT ',' ||
			chr(10) || '  "dbid": '                 || chr(34) || dbid                || chr(34) || ','
		||  chr(10) || '  "dbname": '               || chr(34) || name                || chr(34) || ','
		||  chr(10) || '  "db_unique_name": '       || chr(34) || db_unique_name      || chr(34) || ','
		||  chr(10) || '  "database_role": '        || chr(34) || database_role       || chr(34) || ','
        ||  chr(10) || '  "controlfile_type": '     || chr(34) || controlfile_type    || chr(34) || ','
        ||  chr(10) || '  "controlfile_created": '  || chr(34) || controlfile_created || chr(34) || ','
		||  chr(10) || '  "created": '              || chr(34) || created             || chr(34) 
		INTO v_database FROM v$database;
	END IF;

	SELECT ',' ||
	   	   chr(10) || '  "sockets": ' || COALESCE(to_char(sockets), 'null') || ','
		|| chr(10) || '  "cores": '   || COALESCE(to_char(cores),   'null') || ','
		|| chr(10) || '  "cpus": '    || COALESCE(to_char(cpus),    'null')
	INTO v_osstats
	FROM (SELECT 
		  MAX(CASE WHEN stat_name = 'NUM_CPUS'        THEN value ELSE NULL END) cpus
		, MAX(CASE WHEN stat_name = 'NUM_CPU_CORES'   THEN value ELSE NULL END) cores
		, MAX(CASE WHEN stat_name = 'NUM_CPU_SOCKETS' THEN value ELSE NULL END) sockets
		FROM v$osstat WHERE stat_name in ('NUM_CPUS', 'NUM_CPU_CORES', 'NUM_CPU_SOCKETS')
	);

	IF v_status IN ('OPEN') THEN
		EXECUTE IMMEDIATE 'SELECT COUNT(table_name) statspack FROM all_tables WHERE table_name = ''STATS$SNAPSHOT''' INTO v_statspack;
		EXECUTE IMMEDIATE 
			'SELECT SUM(detected_usages) FROM dba_feature_usage_statistics u1 ' || 
			'WHERE u1.version = (SELECT MAX(u2.version) FROM dba_feature_usage_statistics u2 WHERE u2.name = u1.name) ' ||
			'AND DBID = (SELECT dbid FROM v$database) AND name = ''AWR Report'''
		INTO v_awr;

		SELECT ',' ||
			chr(10) || '  "statspack": ' || v_statspack || ','
		||  chr(10) || '  "awrusage": '  || v_awr
		INTO v_feat FROM DUAL;
	END IF;

	DBMS_OUTPUT.PUT_LINE('{' || chr(10) || v_instance || v_database || v_osstats || v_feat || chr(10) || '}' );
END;
/