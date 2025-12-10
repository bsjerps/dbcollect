PROMPT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PROMPT RESOURCE LIMITS
PROMPT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

COL RESOURCE_NAME       FORMAT A30               HEAD 'Resource'
COL CURRENT_UTILIZATION FORMAT 99999999          HEAD 'Current Utilization'
COL MAX_UTILIZATION     LIKE CURRENT_UTILIZATION HEAD 'Max Utilization'
COL INITIAL_ALLOCATION  LIKE RESOURCE_NAME       HEAD 'Initial Allocation'
COL LIMIT_VALUE         LIKE RESOURCE_NAME       HEAD 'Limit Value'

SELECT resource_name
, current_utilization 
, max_utilization
, initial_allocation
, limit_value
FROM v$resource_limit
/
