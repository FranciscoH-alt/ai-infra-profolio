SELECT * FROM v_revenue_rolling_7d
WHERE date_key BETWEEN :start_date AND :end_date
ORDER BY date_key;
