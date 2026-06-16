import streamlit as st
import pandas as pd

# Create sample data
data = {
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "filters": ["blue", "red", "all", "none", "blue"],
    "options": [
       ( "option_a", "option_b"),
       ( "option_c", "option_d" "option_e"),
       ( "option_a", "option_f"),
       ( "option_b", "option_c"),
       ( "option_d", "option_e", "option_f")
    ]
}

df = pd.DataFrame(data)

# Define column configuration for data editor
column_config = {

    "name": st.column_config.TextColumn("name"),

    "filters": st.column_config.SelectboxColumn(
        "filters",
        options=data["filters"],
        default= "all"
    ),
    "options": st.column_config.MultiselectColumn(
        "options",
        options=["option_a", "option_b", "option_c", "option_d", "option_e", "option_f"]
    )
}

options_df = st.data_editor(
    data,
    column_config=column_config,
    hide_index=True,
    use_container_width=True,

)

st.write(data)

