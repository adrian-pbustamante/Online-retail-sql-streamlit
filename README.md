# Online Retail — SQL + Streamlit

This repo contains an end-to-end demo project: ETL from the Online Retail CSV into SQLite, SQL analysis, and Streamlit dashboard skeleton workflow.

#### Files:
- db.py: SQLite helpers
- etl.py: cleans CSV and populates normalized tables
- queries.sql: useful SQL snippets
- app.py: Streamlit dashboard skeleton (KPIs, cohort, top products, RFM)
- requirements.txt

#### About the ddata

This is a transactional data set which contains all the transactions occurring between 01/12/2010 
and 09/12/2011 for a UK-based and registered non-store online retail.The company mainly sells unique 
all-occasion gifts. Many customers of the company are wholesalers.

the data can be download at: https://archive.ics.uci.edu/dataset/352/online+retail

InvoiceNo: Invoice number. Nominal, a 6-digit integral number uniquely assigned to each transaction. If this code starts with letter 'c', it indicates a cancellation. 

StockCode: Product (item) code. Nominal, a 5-digit integral number uniquely assigned to each distinct product.

Description: Product (item) name. Nominal.

Quantity: The quantities of each product (item) per transaction. Numeric.	

InvoiceDate: Invoice Date and time. Numeric, the day and time when each transaction was generated.

UnitPrice: Unit price. Numeric, Product price per unit in sterling.

CustomerID: Customer number. Nominal, a 5-digit integral 
number uniquely assigned to each customer.

Country: Country name. Nominal, the name of the country where each customer resides. 

#### Setup (Ubuntu):
1. install requirements
   pip install -r requirements.txt
2. run ETL
   python etl.py /path/to/OnlineRetail.csv
3. run Streamlit app
   streamlit run app.py
