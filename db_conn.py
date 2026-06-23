import streamlit as st
import sqlalchemy
import psycopg2
import pandas as pd

def get_conn():

    sql = """SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'"""

    conn = st.connection("cesium_dev", type="sql")  
    query = conn.query(sql=sql)
    return pd.DataFrame(query)["table_name"].tolist()