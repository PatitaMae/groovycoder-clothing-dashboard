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

# Create tabs
tab_overview, tab_products, tab_sales = st.tabs([
    "Overview",
    "Products & Categories",
    "Sales Performance"
])


# =========================================================
# TAB 1: OVERVIEW
# =========================================================
with tab_overview:
    st.subheader("Connection Status & Sample Data")

    st.write("Testing connection to the database...")

    try:
        test_query = "SELECT * FROM Orders LIMIT 10;"
        df_test = run_query(test_query)
        st.success("Connected to RDS successfully! Showing sample data from Orders:")
        st.dataframe(df_test)
    except Exception as e:
        st.error("Error connecting to the database:")
        st.code(str(e))

# =========================================================
# TAB 2: PRODUCTS & CATEGORIES
# =========================================================
with tab_products:
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

    fig_q1 = px.bar(
        df_q1,
        x="SKU",
        y="total_quantity_sold",
        color="product_name",
        title="Top-Selling Products (By Quantity)",
    )
    st.plotly_chart(fig_q1, use_container_width=True)

    # ---------------------------------------------------------
    # Q2: Revenue by Category
    # ---------------------------------------------------------
    st.header("Q2: Revenue by Category")

    q2 = """
    SELECT 
        category_name,
        SUM(total_revenue) AS revenue
    FROM v_variant_sales_summary
    GROUP BY category_name
    ORDER BY revenue DESC;
    """

    df_q2 = run_query(q2)

    st.subheader("Revenue by Category")
    st.dataframe(df_q2)

    fig_q2 = px.bar(
        df_q2,
        x="category_name",
        y="revenue",
        title="Total Revenue by Category",
    )
    st.plotly_chart(fig_q2, use_container_width=True)

# =========================================================
# TAB 3: SALES PERFORMANCE
# =========================================================
with tab_sales:

    # ---------------------------------------------------------
    # Q3: Monthly Revenue Trend
    # ---------------------------------------------------------
    st.header("Q3: Monthly Revenue Trend")

    q3 = """
    SELECT 
        DATE_FORMAT(order_date, '%Y-%m') AS month,
        SUM(total_amount) AS revenue
    FROM Orders
    WHERE status IN ('paid','shipped')
    GROUP BY month
    ORDER BY month;
    """

    df_q3 = run_query(q3)

    st.subheader("Revenue by Month")
    st.dataframe(df_q3)

    fig_q3 = px.line(
        df_q3,
        x="month",
        y="revenue",
        title="Monthly Revenue Trend"
    )
    st.plotly_chart(fig_q3, use_container_width=True)

    # ---------------------------------------------------------
    # Q4: Average Order Value (AOV)
    # ---------------------------------------------------------
    st.header("Q4: Average Order Value (AOV)")

    q4 = """
    SELECT AVG(total_amount) AS aov
    FROM Orders
    WHERE status IN ('paid','shipped');
    """

    df_q4 = run_query(q4)

    aov_value = round(df_q4['aov'][0], 2)

    st.metric(
        label="Average Order Value (AOV)",
        value=f"${aov_value}"
    )
