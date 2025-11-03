SELECT * FROM v_retention_cohorts
WHERE cohort_month BETWEEN :cohort_start AND :cohort_end
ORDER BY cohort_month, active_month;
