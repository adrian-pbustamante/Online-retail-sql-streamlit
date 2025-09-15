
import sys
from pathlib import Path
import pandas as pd
from db import ENGINE
from sqlalchemy import text

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=['CustomerID','InvoiceNo','StockCode','InvoiceDate'])
    df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], dayfirst=True, errors='coerce')
    df = df[df['InvoiceDate'].notna()]
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0).astype(int)
    df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce').fillna(0.0)
    df = df[df['Quantity'] > 0]
    df['CustomerID'] = df['CustomerID'].astype(int)
    df['StockCode'] = df['StockCode'].astype(str)
    df['Description'] = df['Description'].fillna('').str.strip()
    return df

def build_and_load(df: pd.DataFrame):
    with ENGINE.begin() as conn:
        conn.execute(text('DROP TABLE IF EXISTS staging;'))
    df.to_sql('staging', con=ENGINE, if_exists='replace', index=False)

    with ENGINE.begin() as conn:
        conn.execute(text('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY, 
            country TEXT
        );
    '''))
        conn.execute(text('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT UNIQUE,
            description TEXT
        );
        '''))
        conn.execute(text('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            invoice_no TEXT,
            invoice_date TIMESTAMP,
            customer_id INTEGER,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        );
        '''))
        conn.execute(text('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY(order_id) REFERENCES orders(order_id),
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        );
        '''))
        conn.execute(text('''
        INSERT OR IGNORE INTO customers(customer_id, country)
        SELECT DISTINCT CustomerID, Country FROM staging;
        '''))
        conn.execute(text('''
        INSERT OR IGNORE INTO products(stock_code, description)
        SELECT DISTINCT StockCode, Description FROM staging;
        '''))
        conn.execute(text('DELETE FROM orders;'))
        conn.execute(text('''
        INSERT INTO orders(invoice_no, invoice_date, customer_id)
        SELECT DISTINCT InvoiceNo, InvoiceDate, CustomerID FROM staging;
        '''))
        conn.execute(text('''DELETE FROM order_items;'''))
        conn.execute(text('''
        INSERT INTO order_items(order_id, product_id, quantity, unit_price)
        SELECT o.rowid AS order_id, p.product_id, s.Quantity,  s.UnitPrice
        FROM staging s
        JOIN orders o ON o.invoice_no = s.InvoiceNo
        JOIN products p ON p.stock_code = s.StockCode;
        '''))

def main(file_path: str):
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"{file_path} not found")
    df = pd.read_excel(p)
    df = clean_df(df)
    build_and_load(df)
    print('ETL complete — DB at:', Path(__file__).parent / 'data'/ 'online_retail.db')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python etl.py /path/to/Online_Retail.xlsx')
        sys.exit(1)
    main(sys.argv[1])
