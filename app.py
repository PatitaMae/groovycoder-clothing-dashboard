import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# -------------------------
# Database connection setup
# -------------------------

def get_connection():
    conn = mysql.connector.connect(
        host=st.secrets["db_read"]["host"],
        user=st.secrets["db_read"]["user"],
        password=st.secrets["db_read"]["password"],
        database=st.secrets["db_read"]["database"],
        port=st.secrets["db_read"]["port"],
    )
    return conn

def get_write_connection():
    conn = mysql.connector.connect(
        host=st.secrets["db_write"]["host"],
        user=st.secrets["db_write"]["user"],
        password=st.secrets["db_write"]["password"],
        database=st.secrets["db_write"]["database"],
        port=st.secrets["db_write"]["port"],
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

st.title("GroovyCoder Clothing Analytics Dashboard")

# Create tabs
tab_overview, tab_products, tab_sales, tab_customers, tab_prefs, tab_forecast = st.tabs(
    [
        "Overview",
        "Products & Categories",
        "Sales Performance",
        "Customers",
        "Preferences",
        "Demand Forecast"
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
    # DEMO SALES TOOLS
    # =========================================================
    st.subheader("Demo Sales Tools")

    if st.button("Generate Demo Sales Order"):
        try:
            import random
            from datetime import datetime, timedelta

            conn = get_write_connection()
            cur = conn.cursor()

            # -------------------------------
            # 1) Create or retrieve demo user
            # -------------------------------
            demo_email = "button_demo@groovycoder.test"
            cur.execute("SELECT user_id FROM Users WHERE email = %s", (demo_email,))
            row = cur.fetchone()

            if row:
                user_id = row[0]
            else:
                cur.execute(
                    """
                    INSERT INTO Users (first_name, last_name, email, phone, password_hash, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    ("Button", "Demo", demo_email, "555-0300", "dummyhash", "customer"),
                )
                user_id = cur.lastrowid

            # -------------------------------
            # 2) Create or retrieve addresses
            # -------------------------------
            def get_or_create_address(user_id, type_):
                cur.execute(
                    "SELECT address_id FROM Addresses WHERE user_id = %s AND address_type = %s LIMIT 1",
                    (user_id, type_),
                )
                row = cur.fetchone()
                if row:
                    return row[0]

                cur.execute(
                    """
                    INSERT INTO Addresses
                    (user_id, street, city, state, zip, country, address_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, "1 Demo Plaza", "San Diego", "CA", "92101", "USA", type_),
                )
                return cur.lastrowid

            ship_id = get_or_create_address(user_id, "shipping")
            bill_id = get_or_create_address(user_id, "billing")

            # -------------------------------
            # 3) Select random in-stock variant
            # -------------------------------
            cur.execute(
                """
                SELECT pv.variant_id, pv.retail_price, pv.stock_quantity, pv.color, pv.size
                FROM ProductVariants pv
                WHERE pv.active = 1 AND pv.stock_quantity > 0
                ORDER BY RAND()
                LIMIT 1
                """
            )
            row = cur.fetchone()

            if not row:
                st.error("No variants with stock remaining. Cannot generate demo sale.")
                conn.close()
                st.stop()

            variant_id, price, stock, color, size = row

            # -------------------------------
            # 4) Random quantity (1–3)
            # -------------------------------
            quantity = random.randint(1, min(3, stock))
            line_total = round(float(price) * quantity, 2)
            tax = round(line_total * 0.08, 2)

            total = line_total + tax

            # -------------------------------
            # 5) Random timestamp (within last 6 months)
            # -------------------------------
            ts = datetime.utcnow() - timedelta(days=random.randint(0, 180))
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

            # -------------------------------
            # 6) Random order status
            # -------------------------------
            status = random.choice(["paid", "shipped"])

            # -------------------------------
            # 7) Insert order
            # -------------------------------
            cur.execute(
                """
                INSERT INTO Orders
                (user_id, shipping_address_id, billing_address_id,
                 order_date, status, subtotal, tax_amount, total_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, ship_id, bill_id, ts_str, status, line_total, tax, total),
            )
            order_id = cur.lastrowid

            # -------------------------------
            # 8) Insert order item
            # -------------------------------
            cur.execute(
                """
                INSERT INTO OrderItems
                (order_id, variant_id, quantity, unit_price, line_total)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (order_id, variant_id, quantity, price, line_total),
            )

            # -------------------------------
            # 9) Reduce stock
            # -------------------------------
            cur.execute(
                """
                UPDATE ProductVariants
                SET stock_quantity = stock_quantity - %s
                WHERE variant_id = %s
                """,
                (quantity, variant_id),
            )

            conn.commit()
            conn.close()

            st.success(
                f"Random order created! Variant {variant_id} ({color or 'N/A'} / {size or 'N/A'}), "
                f"qty {quantity}, total ${total:.2f} 🎉"
            )

        except Exception as ex:
            st.error("Failed to generate demo sales data.")
            st.code(str(ex))

    # =========================================================
    # UNDO DEMO SALES BUTTON
    # =========================================================
    if st.button("Undo Demo Sales Orders"):
        try:
            conn = get_write_connection()
            cur = conn.cursor()

            demo_email = "button_demo@groovycoder.test"

            # 1. Find demo user
            cur.execute("SELECT user_id FROM Users WHERE email=%s", (demo_email,))
            row = cur.fetchone()

            if row:
                user_id = row[0]

                # 2. Restore stock
                cur.execute(
                    """
                    SELECT oi.variant_id, SUM(oi.quantity)
                    FROM OrderItems oi
                    JOIN Orders o ON oi.order_id = o.order_id
                    WHERE o.user_id = %s
                    GROUP BY oi.variant_id
                    """, (user_id,)
                )
                for variant_id, qty in cur.fetchall():
                    cur.execute(
                        "UPDATE ProductVariants SET stock_quantity = stock_quantity + %s WHERE variant_id = %s",
                        (qty, variant_id),
                    )

                # 3. Delete audit rows
                cur.execute(
                    """
                    DELETE FROM OrderItemsAudit
                    WHERE order_id IN (SELECT order_id FROM Orders WHERE user_id = %s)
                    """, (user_id,)
                )

                # 4. Delete order items
                cur.execute(
                    """
                    DELETE FROM OrderItems
                    WHERE order_id IN (SELECT order_id FROM Orders WHERE user_id = %s)
                    """, (user_id,)
                )

                # 5. Delete orders
                cur.execute("DELETE FROM Orders WHERE user_id = %s", (user_id,))

                # 6. Delete addresses
                cur.execute("DELETE FROM Addresses WHERE user_id = %s", (user_id,))

                # 7. Delete demo user
                cur.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))

            conn.commit()
            conn.close()
            st.success("Demo sales data removed and inventory restored ✅")

        except Exception as ex:
            st.error("Failed to undo demo sales data.")
            st.code(str(ex))
    
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

    # Handle case where no orders exist
    if df_q4["aov"].isna().all():
        st.warning("No paid or shipped orders found — cannot compute AOV yet.")
    else:
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
        import numpy as np
        from sklearn.linear_model import LinearRegression
        import plotly.graph_objects as go

        # month as datetime + label
        df["month"] = pd.to_datetime(df["month"])
        df["month_label"] = df["month"].dt.strftime("%Y-%m")

        # numeric index for regression
        df["month_index"] = range(len(df))  # 0, 1, 2, ...

        # ----------------------------------------
        # 3. Fit Linear Regression
        # ----------------------------------------
        X = df[["month_index"]]
        y = df["units_sold"]

        model = LinearRegression()
        model.fit(X, y)

        # ----------------------------------------
        # 4. Forecast next 3 months
        # ----------------------------------------
        future_steps = 3
        future_index = np.arange(len(df), len(df) + future_steps)

        # generate future month labels
        last_month = df["month"].max()
        future_months = [
            (last_month + pd.DateOffset(months=i)).strftime("%Y-%m")
            for i in range(1, future_steps + 1)
        ]

        forecast = model.predict(future_index.reshape(-1, 1))

        df_forecast = pd.DataFrame({
            "month_index": future_index,
            "forecast_units_sold": forecast,
            "month_label": future_months
        })

        # simple +/- 10% confidence band (for visualization)
        df_forecast["upper"] = df_forecast["forecast_units_sold"] * 1.10
        df_forecast["lower"] = df_forecast["forecast_units_sold"] * 0.90

        # ----------------------------------------
        # 5. Display results
        # ----------------------------------------
        st.subheader("Historical Monthly Sales")
        st.dataframe(df[["month_label", "units_sold"]].rename(columns={"month_label": "month"}))

        st.subheader("Forecast for Next 3 Months")
        st.dataframe(df_forecast[["month_label", "forecast_units_sold"]].rename(
            columns={"month_label": "month"}
        ))

        # ----------------------------------------
        # 6. Plot Results with confidence band
        # ----------------------------------------
        hist_plot = df[["month_label", "units_sold"]].rename(
            columns={"month_label": "month", "units_sold": "value"}
        )
        fore_plot = df_forecast[["month_label", "forecast_units_sold"]].rename(
            columns={"month_label": "month", "forecast_units_sold": "value"}
        )

        fig = go.Figure()

        # historical line
        fig.add_trace(
            go.Scatter(
                x=hist_plot["month"],
                y=hist_plot["value"],
                mode="lines+markers",
                name="Historical"
            )
        )

        # forecast line
        fig.add_trace(
            go.Scatter(
                x=fore_plot["month"],
                y=fore_plot["value"],
                mode="lines+markers",
                name="Forecast"
            )
        )

        # confidence band (upper then lower with fill)
        fig.add_trace(
            go.Scatter(
                x=df_forecast["month_label"],
                y=df_forecast["upper"],
                mode="lines",
                name="Forecast upper (+10%)",
                showlegend=False
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_forecast["month_label"],
                y=df_forecast["lower"],
                mode="lines",
                fill="tonexty",
                name="Forecast lower (-10%)",
                showlegend=False
            )
        )

        fig.update_layout(title="Monthly Sales Forecast", xaxis_title="Month", yaxis_title="Units Sold")

        st.plotly_chart(fig, use_container_width=True)

        # ----------------------------------------
        # 7. Download CSV button
        # ----------------------------------------
        csv = df_forecast[["month_label", "forecast_units_sold"]].rename(
            columns={"month_label": "month"}
        ).to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Forecast as CSV",
            data=csv,
            file_name="forecast_results.csv",
            mime="text/csv",
        )

        # ----------------------------------------
        # 8. Model description
        # ----------------------------------------
        st.caption(
            "The forecast is generated using a Linear Regression model trained on historical "
            "monthly unit sales. The shaded area represents a simple ±10% band around the "
            "point forecast for illustration."
        )
