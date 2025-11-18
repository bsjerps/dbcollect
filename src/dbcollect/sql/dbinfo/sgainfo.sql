PROMPT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PROMPT SGA INFO
PROMPT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

COL NAME       FORMAT A32                 HEAD 'Name'
COL BYTES      FORMAT 999,999,999,999,990 HEAD 'Bytes'
COL RESIZeABLE FORMAT A10                 HEAD 'Resizable'

SELECT name, bytes, resizeable
FROM V$SGAINFO
/
