-- Dimensions
CREATE TABLE IF NOT EXISTS dim_date (
  date_key        date PRIMARY KEY,
  year            int,
  quarter         int,
  month           int,
  day             int,
  iso_week        int
);

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_id     bigserial PRIMARY KEY,
  email           text UNIQUE,
  signup_date     date,
  country         text,
  segment         text
);

CREATE TABLE IF NOT EXISTS dim_product (
  product_id      bigserial PRIMARY KEY,
  sku             text UNIQUE,
  name            text,
  category        text,
  unit_cost       numeric(12,2)
);

-- Facts
CREATE TABLE IF NOT EXISTS fact_orders (
  order_id        bigserial PRIMARY KEY,
  order_ts        timestamp not null,
  date_key        date not null REFERENCES dim_date(date_key),
  customer_id     bigint REFERENCES dim_customer(customer_id),
  status          text check (status in ('paid','refunded','pending','cancelled')),
  subtotal        numeric(12,2) not null,
  discount        numeric(12,2) default 0,
  tax             numeric(12,2) default 0,
  shipping        numeric(12,2) default 0,
  total           numeric(12,2) not null
);

CREATE TABLE IF NOT EXISTS fact_order_items (
  order_item_id   bigserial PRIMARY KEY,
  order_id        bigint references fact_orders(order_id) on delete cascade,
  product_id      bigint references dim_product(product_id),
  quantity        int not null check (quantity > 0),
  unit_price      numeric(12,2) not null,
  line_total      numeric(12,2) generated always as (quantity * unit_price) stored
);

-- Optional generic events (web/app/product usage)
CREATE TABLE IF NOT EXISTS fact_events (
  event_id        bigserial PRIMARY KEY,
  event_ts        timestamp not null,
  date_key        date not null references dim_date(date_key),
  customer_id     bigint references dim_customer(customer_id),
  event_name      text not null,      -- e.g., session_start, add_to_cart, etc.
  event_value     numeric(12,4),
  meta            jsonb               -- flexible payload
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_orders_date ON fact_orders(date_key);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_items_order ON fact_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product ON fact_order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_events_date ON fact_events(date_key);
CREATE INDEX IF NOT EXISTS idx_events_customer ON fact_events(customer_id);

-- Daily revenue view (clean KPI surface)
CREATE OR REPLACE VIEW v_daily_revenue AS
SELECT
  fo.date_key,
  sum(CASE WHEN fo.status='paid' THEN fo.total ELSE 0 END)  AS revenue,
  sum(CASE WHEN fo.status='refunded' THEN fo.total ELSE 0 END) AS refunds,
  count(*) FILTER (WHERE fo.status='paid') AS orders_paid,
  count(*) AS orders_all
FROM fact_orders fo
GROUP BY fo.date_key;

-- Rolling 7-day revenue (window function)
CREATE OR REPLACE VIEW v_revenue_rolling_7d AS
SELECT
  date_key,
  revenue,
  sum(revenue) OVER (ORDER BY date_key ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS revenue_rolling_7d
FROM v_daily_revenue
ORDER BY date_key;

-- Top products (last 30 days)
CREATE OR REPLACE VIEW v_top_products_30d AS
WITH recent AS (
  SELECT * FROM fact_orders WHERE order_ts >= now() - interval '30 days' AND status='paid'
)
SELECT
  p.product_id,
  p.name,
  p.category,
  sum(oi.quantity) AS units,
  sum(oi.line_total) AS sales
FROM recent r
JOIN fact_order_items oi ON oi.order_id = r.order_id
JOIN dim_product p ON p.product_id = oi.product_id
GROUP BY 1,2,3
ORDER BY sales DESC;

-- Basic retention cohorts (signup month x return month)
CREATE OR REPLACE VIEW v_retention_cohorts AS
WITH firsts AS (
  SELECT c.customer_id, date_trunc('month', c.signup_date)::date AS cohort_month
  FROM dim_customer c
),
activity AS (
  SELECT customer_id, date_trunc('month', order_ts)::date AS active_month
  FROM fact_orders
  WHERE status='paid'
  GROUP BY 1,2
)
SELECT
  f.cohort_month,
  a.active_month,
  count(DISTINCT a.customer_id) AS active_customers
FROM firsts f
LEFT JOIN activity a ON a.customer_id = f.customer_id
GROUP BY 1,2
ORDER BY 1,2;

-- Materialized daily metrics for speed
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_metrics AS
SELECT
  d.date_key,
  coalesce(v.revenue,0) AS revenue,
  coalesce(v.refunds,0) AS refunds,
  coalesce(v.orders_paid,0) AS orders_paid,
  COUNT(DISTINCT fo.customer_id) FILTER (WHERE fo.status='paid') AS paying_customers
FROM dim_date d
LEFT JOIN v_daily_revenue v USING (date_key)
LEFT JOIN fact_orders fo USING (date_key)
GROUP BY 1,2,3,4
WITH NO DATA;

-- For faster refresh without locking readers:
CREATE INDEX IF NOT EXISTS idx_mv_daily_metrics_date ON mv_daily_metrics(date_key);
