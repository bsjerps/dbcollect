PROMPT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PROMPT ASM DISK DETAIL
PROMPT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

COL DISKNAME            FORMAT A30      HEAD 'Disk name'
COL DG_NAME             FORMAT A30      HEAD 'Diskgroup'
COL FAILGROUP           LIKE DG_NAME    HEAD 'Failgroup'
COL STATE               FORMAT A8       HEAD 'State'
COL MODE_STATUS         FORMAT A8       HEAD 'Mode'
COL CREATED                             HEAD 'Created'
COL MOUNTED                             HEAD 'Mounted'
COL LIBRARY             FORMAT A20      HEAD 'Library'
COL LABEL               FORMAT A30      HEAD 'Label'
COL PRODUCT             FORMAT A30      HEAD 'Product'
COL PSZ                 FORMAT 9999     HEAD 'PSZ'
COL LSZ                 LIKE PSZ        HEAD 'LSZ'
COL PREFERRED           FORMAT A10      HEAD 'Preferred'
COL THIN                FORMAT A5       HEAD 'Thin'
COL PATH                FORMAT A120     HEAD 'Path'

SELECT d.name                      diskname
, COALESCE(dg.name, header_status) dg_name
, failgroup
, mode_status
, d.state
, create_date                      created
, mount_date                       mounted
, library
, label
, product
, d.SECTOR_SIZE               PSZ
, d.LOGICAL_SECTOR_SIZE       LSZ -- 12.2+
, THIN_PROVISION_CAPABLE thin -- 12.2+
, DECODE(PREFERRED_READ,'U','UNSET','Y','Yes','N','No','UNKNOWN') PREFERRED
, path
FROM gv$asm_disk d
LEFT OUTER JOIN v$asm_diskgroup dg USING (group_number)
JOIN v$instance ON inst_id=instance_number
WHERE group_number <> 0
ORDER BY d.name, path
/

CLEAR COMPUTES COLUMNS
