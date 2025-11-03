SELECT
  date_key,
  revenue,
  refunds,
  orders_paid,
  paying_customers,
  CASE WHEN revenue <> 0 THEN refunds / revenue ELSE 0 END AS refund_rate
FROM mv_daily_metrics
WHERE date_key BETWEEN :start_date AND :end_date
ORDER BY date_key;
