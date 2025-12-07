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
tab_overview, tab_products, tab_sales, tab_customers, tab_prefs, tab_forecast = st.tabs(
    [
        "Overview",
        "Products & Categories",
        "Sales Performance",
        "Customers",
        "Preferences",
        "📈 Demand Forecast"
    ]
)

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

    fig_q3 = px.bar(
        df_q3,
        x="month",
        y="revenue",
        title="Monthly Revenue Trend",
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

    aov_value = round(df_q4["aov"][0], 2)

    st.metric(
        label="Average Order Value (AOV)",
        value=f"${aov_value}",
    )

# =========================================================
# TAB 4: CUSTOMERS
# =========================================================
with tab_customers:
    # ---------------------------------------------------------
    # Q5: Top Customers by Spend
    # ---------------------------------------------------------
    st.header("Q5: Top Customers by Spend")

    q5 = """
    SELECT 
        u.user_id,
        CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(o.total_amount) AS total_spent
    FROM Orders o
    JOIN Users u ON o.user_id = u.user_id
    WHERE o.status IN ('paid','shipped')
    GROUP BY u.user_id, customer_name
    ORDER BY total_spent DESC
    LIMIT 10;
    """

    df_q5 = run_query(q5)

    st.subheader("Top 10 Customers by Total Spend")
    st.dataframe(df_q5)

    fig_q5 = px.bar(
        df_q5,
        x="customer_name",
        y="total_spent",
        title="Top Customers by Total Revenue",
    )
    st.plotly_chart(fig_q5, use_container_width=True)

# =========================================================
# TAB 5: PREFERENCES (Sizes, Colors, Day of Week)
# =========================================================
with tab_prefs:
    # ---------------------------------------------------------
    # Q6: Popular Sizes
    # ---------------------------------------------------------
    st.header("Q6: Popular Sizes")

    q6 = """
    SELECT 
        pv.size,
        SUM(oi.quantity) AS total_quantity
    FROM OrderItems oi
    JOIN ProductVariants pv ON oi.variant_id = pv.variant_id
    GROUP BY pv.size
    ORDER BY total_quantity DESC;
    """

    df_q6 = run_query(q6)

    st.subheader("Units Sold by Size")
    st.dataframe(df_q6)

    fig_q6 = px.bar(
        df_q6,
        x="size",
        y="total_quantity",
        title="Most Popular Sizes",
    )
    st.plotly_chart(fig_q6, use_container_width=True)

    # ---------------------------------------------------------
    # Q7: Popular Colors
    # ---------------------------------------------------------
    st.header("Q7: Popular Colors")

    q7 = """
    SELECT 
        pv.color,
        SUM(oi.quantity) AS total_quantity
    FROM OrderItems oi
    JOIN ProductVariants pv ON oi.variant_id = pv.variant_id
    GROUP BY pv.color
    ORDER BY total_quantity DESC;
    """

    df_q7 = run_query(q7)

    st.subheader("Units Sold by Color")
    st.dataframe(df_q7)

    fig_q7 = px.bar(
        df_q7,
        x="color",
        y="total_quantity",
        title="Most Popular Colors",
    )
    st.plotly_chart(fig_q7, use_container_width=True)

    # ---------------------------------------------------------
    # Q8: Sales by Day of Week
    # ---------------------------------------------------------
    st.header("Q8: Sales by Day of Week")

    q8 = """
    SELECT 
        DAYNAME(order_date) AS day_name,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM Orders
    WHERE status IN ('paid','shipped')
    GROUP BY day_name
    ORDER BY FIELD(day_name, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday');
    """

    df_q8 = run_query(q8)

    st.subheader("Orders and Revenue by Day of Week")
    st.dataframe(df_q8)

    fig_q8 = px.bar(
        df_q8,
        x="day_name",
        y="revenue",
        title="Revenue by Day of Week",
    )
    st.plotly_chart(fig_q8, use_container_width=True)

# =========================================================
# TAB 6: DEMAND FORECASTING
# =========================================================

with tab_forecast:
    st.header("Monthly Demand Forecast (Linear Regression)")

    # ----------------------------------------
    # 1. SQL: Get monthly sales from database
    # ----------------------------------------
    query_forecast = """
    SELECT 
        DATE_FORMAT(o.order_date, '%Y-%m') AS month,
        SUM(oi.quantity) AS units_sold
    FROM Orders o
    JOIN OrderItems oi ON o.order_id = oi.order_id
    WHERE o.status IN ('paid','shipped')
    GROUP BY month
    ORDER BY month;
    """

    df = run_query(query_forecast)

    if df.empty:
        st.warning("Not enough sales data to create a forecast yet.")
    else:
        # ----------------------------------------
        # 2. Prepare data
        # ----------------------------------------
        df['month_index'] = range(len(df))  # 0, 1, 2, ...

        # ----------------------------------------
        # 3. Fit Linear Regression
        # ----------------------------------------
        from sklearn.linear_model import LinearRegression
        import numpy as np

        X = df[['month_index']]
        y = df['units_sold']

        model = LinearRegression()
        model.fit(X, y)

        # ----------------------------------------
        # 4. Forecast next 3 months
        # ----------------------------------------
        future_steps = 3
        future_index = np.arange(len(df), len(df) + future_steps)

        forecast = model.predict(future_index.reshape(-1, 1))

        df_forecast = pd.DataFrame({
            'month_index': future_index,
            'forecast_units_sold': forecast
        })

        # ----------------------------------------
        # 5. Display results
        # ----------------------------------------
        st.subheader("Historical Monthly Sales")
        st.dataframe(df)

        st.subheader("Forecast for Next 3 Months")
        st.dataframe(df_forecast)

        # ----------------------------------------
        # 6. Plot Results
        # ----------------------------------------
        import plotly.express as px

        # Combine for plotting
        df_plot = pd.concat([
            df[['month_index', 'units_sold']]
              .rename(columns={'units_sold': 'value'})
              .assign(type='Historical'),

            df_forecast
              .rename(columns={'forecast_units_sold': 'value'})
              .assign(type='Forecast')
        ])

        fig = px.line(
            df_plot,
            x="month_index",
            y="value",
            color="type",
            markers=True,
            title="Monthly Sales Forecast"
        )

        st.plotly_chart(fig, use_container_width=True)
