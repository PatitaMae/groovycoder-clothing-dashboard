import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# -------------------------
# Database connection setup
# -------------------------

def get_connection():
    conn = mysql.connector.connect(
        host=st.secrets["db"]["host"],
        user=st.secrets["db"]["user"],
        password=st.secrets["db"]["password"],
        database=st.secrets["db"]["database"],
        port=st.secrets["db"]["port"],
    )
    return conn

def run_query(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# -------------------------
# Streamlit UI
# -------------------------

st.title("GroovyCoder Clothing – Analytics Dashboard")

st.write("Testing connection to the database...")

try:
    # Simple test: show first 10 orders (adjust table name if needed)
    test_query = "SELECT * FROM Orders LIMIT 10;"
    df_test = run_query(test_query)
    st.success("Connected to RDS successfully! Showing sample data from Orders:")
    st.dataframe(df_test)
except Exception as e:
    st.error("Error connecting to the database:")
    st.code(str(e))
