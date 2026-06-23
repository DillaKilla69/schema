from pandas.core.frame import DataFrame
import streamlit as st
from typing import Any

from sql_compiler import CompiledSQL

def query_db(sql:str, params: dict[str, Any]) -> DataFrame:
    conn = st.connection("cesium_dev", type="sql")

    return conn.query(sql=sql, params=params)
