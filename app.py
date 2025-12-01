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

# ---------------------------------------------------------
# Q1: Top-Selling Products by Quantity
# ---------------------------------------------------------

st.header("Q1: Top-Selling Products (By Quantity Sold)")

q1 = """
SELECT 
    p.product_name,
    pv.SKU,
    pv.color,
    pv.size,
    SUM(oi.quantity) AS total_quantity_sold
FROM OrderItems oi
JOIN ProductVariants pv ON oi.variant_id = pv.variant_id
JOIN Products p ON pv.product_id = p.product_id
GROUP BY p.product_name, pv.SKU, pv.color, pv.size
ORDER BY total_quantity_sold DESC
LIMIT 10;
"""

df_q1 = run_query(q1)

st.subheader("Top 10 Best-Selling Variants")
st.dataframe(df_q1)

# Bar chart
import plotly.express as px
fig_q1 = px.bar(
    df_q1,
    x="SKU",
    y="total_quantity_sold",
    color="product_name",
    title="Top-Selling Products (By Quantity)",
)
st.plotly_chart(fig_q1, use_container_width=True)