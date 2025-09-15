
import streamlit as st
import pandas as pd
import plotly.express as px
from db import run_sql

from pathlib import Path
import streamlit as st
from etl import main as etl_main

# paths (adjust if your layout differs)
ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "online_retail.db"
xlsx_PATH = ROOT / "data" / "Online-Retail.xlsx"  

def ensure_db():
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        st.info("Building local database — running ETL. This may take a moment...")
        try:
            etl_main(str(xlsx_PATH))
            st.success("ETL complete.")
        except FileNotFoundError as e:
            st.error(f"ETL failed: {e}")
            st.stop()
        except Exception as e:
            st.error(f"ETL error: {e}")
            st.stop()

ensure_db()


st.set_page_config(layout='wide', page_title='Online Retail Analytics')
st.title('Online Retail — SQL & Streamlit. Author: Adrian P. Bustamante. email: adrianpebus@gmail.com')
st.markdown('Dataset: Online Retail (transactions). ETL -> SQLite -> Streamlit.')

# KPIs
kpi_q = '''
SELECT
  COALESCE(SUM(oi.quantity * oi.unit_price),0) AS revenue,
  COUNT(DISTINCT o.order_id) AS orders,
  COUNT(DISTINCT o.customer_id) AS customers,
  AVG(oi.quantity * oi.unit_price) AS avg_order_value
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id;
'''
kpis = run_sql(kpi_q).iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric('Revenue', f"${kpis.revenue:,.0f}")
c2.metric('Orders', int(kpis.orders))
c3.metric('Customers', int(kpis.customers))
c4.metric('Avg Order Value', f"${kpis.avg_order_value:,.2f}")

st.markdown('---')

# Date range filter
dates = run_sql('SELECT MIN(invoice_date) AS min_date, MAX(invoice_date) AS max_date FROM orders;').iloc[0]
min_date = pd.to_datetime(dates.min_date)
max_date = pd.to_datetime(dates.max_date)
start, end = st.date_input('Date range', value=(min_date.date(), max_date.date()), min_value=min_date.date(), max_value=max_date.date())

# Monthly revenue chart
mrev_q = '''
SELECT strftime('%Y-%m', o.invoice_date) AS month,
       SUM(oi.quantity * oi.unit_price) AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE date(o.invoice_date) BETWEEN :start AND :end
GROUP BY month
ORDER BY month;
'''
mrev = run_sql(mrev_q, {"start": start.isoformat(), "end": end.isoformat()})
if not mrev.empty:
    fig = px.line(mrev, x='month', y='revenue', title='Monthly Revenue')
    st.plotly_chart(fig, use_container_width=True)

# Top products
st.markdown('### Top products by revenue')
topn = st.slider('Top N products', 5, 50, 10)
top_q = '''
SELECT p.product_id, p.description,
       SUM(oi.quantity * oi.unit_price) AS revenue,
       SUM(oi.quantity) AS total_qty
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE date(o.invoice_date) BETWEEN :start AND :end
GROUP BY p.product_id, p.description
ORDER BY revenue DESC
LIMIT :topn;
'''
top = run_sql(top_q, {"start": start.isoformat(), "end": end.isoformat(), "topn": topn})
st.dataframe(top)

st.markdown('---')

# Cohort heatmap
st.markdown('### Cohort retention heatmap')
cohort_q = '''
WITH first_order AS (
  SELECT customer_id, MIN(strftime('%Y-%m', invoice_date)) AS cohort_month
  FROM orders
  GROUP BY customer_id
),
customer_orders AS (
  SELECT customer_id, strftime('%Y-%m', invoice_date) AS order_month
  FROM orders
)
SELECT f.cohort_month, c.order_month,
       COUNT(DISTINCT c.customer_id) AS active_customers
FROM first_order f
JOIN customer_orders c USING(customer_id)
GROUP BY f.cohort_month, c.order_month
ORDER BY f.cohort_month, c.order_month;
'''
cohort_df = run_sql(cohort_q)
if not cohort_df.empty:
    cohort_df['cohort_month'] = pd.to_datetime(cohort_df['cohort_month'] + '-01')
    cohort_df['order_month'] = pd.to_datetime(cohort_df['order_month'] + '-01')
    cohort_df['month_offset'] = ((cohort_df['order_month'].dt.year - cohort_df['cohort_month'].dt.year) * 12 + (cohort_df['order_month'].dt.month - cohort_df['cohort_month'].dt.month))
    pivot = cohort_df.pivot_table(index='cohort_month', columns='month_offset', values='active_customers', aggfunc='sum').fillna(0)
    cohort_sizes = pivot.iloc[:, 0]
    retention = pivot.divide(cohort_sizes, axis=0).clip(0,1)
    fig = px.imshow(retention, labels=dict(x='Months since cohort', y='Cohort month', color='Retention'), x=retention.columns, y=retention.index.strftime('%Y-%m'))
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')
st.markdown('### RFM top customers (sample)')
rfm_q = '''
WITH latest AS (SELECT MAX(invoice_date) AS max_date FROM orders),
cust AS (
  SELECT o.customer_id,
         CAST((julianday((SELECT max_date FROM latest)) - julianday(MAX(o.invoice_date))) AS INTEGER) AS recency,
         COUNT(DISTINCT o.order_id) AS frequency,
         SUM(oi.quantity * oi.unit_price) AS monetary
  FROM orders o
  JOIN order_items oi ON o.order_id = oi.order_id
  GROUP BY o.customer_id
)
SELECT customer_id, recency, frequency, monetary
FROM cust
ORDER BY monetary DESC
LIMIT 50;
'''
rfm = run_sql(rfm_q)
st.dataframe(rfm)

st.markdown('---')
st.markdown('GitHub: https://github.com/adrian-pbustamante/Online-retail-sql-streamlit | Live app: https://online-retail-sql-streaml.streamlit.app/')
