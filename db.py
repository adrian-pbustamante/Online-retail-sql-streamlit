
from sqlalchemy import create_engine, text
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data' / 'online_retail.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

def run_sql(query: str, params: dict = None) -> pd.DataFrame:
    with ENGINE.connect() as conn:
        return pd.read_sql_query(text(query), conn, params=params)

def execute_script(script: str):
    with ENGINE.begin() as conn:
        conn.execute(text(script))

if __name__ == '__main__':
    print('DB helpers ready. DB file:', DB_PATH)
