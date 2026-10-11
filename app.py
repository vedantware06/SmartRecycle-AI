
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

st.set_page_config(
    page_title="SmartRecycle AI",
    page_icon="♻️",
    layout="wide"
)

DB_FILE = "smartrecycle.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def setup_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT,
                transaction_type TEXT,
                material TEXT,
                quantity REAL,
                rate REAL,
                total REAL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS market_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price_date TEXT,
                material TEXT,
                rate REAL,
                source TEXT
            )
        """)


def load_transactions():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM transactions ORDER BY id DESC",
            conn
        )


def load_prices():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM market_prices ORDER BY price_date DESC, id DESC",
            conn
        )


setup_database()

st.title("♻️ SmartRecycle AI")
st.subheader("Recycling Business Intelligence Dashboard")

page = st.sidebar.radio(
    "Select Section",
    [
        "Dashboard",
        "Add Purchase / Sale",
        "Transaction History",
        "Market Prices",
        "Stock Management"
    ]
)


# ADD TRANSACTION
if page == "Add Purchase / Sale":
    st.header("📝 Add Business Transaction")

    with st.form("transaction_form"):
        entry_date = st.date_input("Date", value=date.today())

        transaction_type = st.selectbox(
            "Transaction Type", ["Purchase", "Sale"]
        )

        material = st.selectbox(
            "Material",
            ["Plastic", "Paper", "Metal", "Glass", "Other"]
        )

        quantity = st.number_input(
            "Quantity (kg)", min_value=0.1, value=10.0
        )

        rate = st.number_input(
            "Rate (₹ per kg)", min_value=0.0, value=10.0
        )

        submitted = st.form_submit_button("Save Transaction")

        if submitted:
            total = quantity * rate

            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO transactions
                    (entry_date, transaction_type, material,
                     quantity, rate, total)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(entry_date), transaction_type, material,
                        quantity, rate, total
                    )
                )

            st.success(
                f"{transaction_type} saved! Total: ₹{total:,.2f}"
            )
            st.rerun()


# TRANSACTION HISTORY
elif page == "Transaction History":
    st.header("📚 Saved Transactions")

    transactions = load_transactions()

    if transactions.empty:
        st.info("No transactions saved yet.")
    else:
        st.dataframe(
            transactions,
            use_container_width=True,
            hide_index=True
        )

        csv_data = transactions.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Transactions CSV",
            data=csv_data,
            file_name="smartrecycle_transactions.csv",
            mime="text/csv"
        )


# MARKET PRICES
elif page == "Market Prices":
    st.header("🌐 Scrap Market Price Tracker")

    st.write(
        "वेबसाइटवर दर तपासा आणि तारीख, दर व स्रोत database मध्ये सेव्ह करा."
    )

    st.markdown(
        "[Recyclo India — Published Scrap Prices]"
        "(https://www.recycloindia.com/)"
    )

    st.markdown(
        "[Scrapprice — Material Price List]"
        "(https://www.scrapprice.in/scrap-materials)"
    )

    st.warning(
        "दर वेबसाइटवरून आपोआप घेतले जात नाहीत. "
        "तपासलेला दर स्वतः भरावा लागतो."
    )

    with st.form("market_form"):
        price_date = st.date_input(
            "Price checked on", value=date.today()
        )

        market_material = st.selectbox(
            "Material",
            [
                "Plastic", "Paper", "Metal", "Glass",
                "Copper", "Aluminium", "Iron",
                "PET Bottles", "Other"
            ]
        )

        market_rate = st.number_input(
            "Published rate (₹ per kg)",
            min_value=0.0,
            value=0.0
        )

        source = st.text_input(
            "Source website URL",
            placeholder="Paste the webpage URL"
        )

        save_price = st.form_submit_button("Save Market Price")

        if save_price:
            if market_rate <= 0 or not source.strip():
                st.error("Valid rate आणि source URL भरा.")
            else:
                with get_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO market_prices
                        (price_date, material, rate, source)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            str(price_date),
                            market_material,
                            market_rate,
                            source.strip()
                        )
                    )

                st.success("Market price saved in database!")
                st.rerun()

    st.subheader("📋 Saved Market Prices")
    prices = load_prices()

    if prices.empty:
        st.info("Market prices अजून सेव्ह केलेले नाहीत.")
    else:
        st.dataframe(
            prices,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("📈 Market Price Trend")

        trend = (
            prices.groupby(["price_date", "material"])["rate"]
            .mean()
            .unstack()
            .sort_index()
        )

        st.line_chart(trend)

        csv_prices = prices.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Market Prices CSV",
            data=csv_prices,
            file_name="smartrecycle_market_prices.csv",
            mime="text/csv"
        )


# STOCK MANAGEMENT - NEW FEATURE
elif page == "Stock Management":
    st.header("📦 Stock Management")

    transactions = load_transactions()

    if transactions.empty:
        st.info("Stock पाहण्यासाठी आधी Purchase किंवा Sale नोंदवा.")
    else:
        purchases = transactions[
            transactions["transaction_type"] == "Purchase"
        ]

        sales = transactions[
            transactions["transaction_type"] == "Sale"
        ]

        purchase_qty = purchases.groupby("material")["quantity"].sum()
        sales_qty = sales.groupby("material")["quantity"].sum()

        stock = pd.DataFrame({
            "Total Purchased (kg)": purchase_qty,
            "Total Sold (kg)": sales_qty
        }).fillna(0)

        stock["Available Stock (kg)"] = (
            stock["Total Purchased (kg)"] - stock["Total Sold (kg)"]
        )

        stock = stock.reset_index()
        stock = stock.rename(columns={"material": "Material"})

        total_purchased = stock["Total Purchased (kg)"].sum()
        total_sold = stock["Total Sold (kg)"].sum()
        total_available = stock["Available Stock (kg)"].sum()

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Purchased", f"{total_purchased:,.1f} kg")
        c2.metric("Total Sold", f"{total_sold:,.1f} kg")
        c3.metric("Available Stock", f"{total_available:,.1f} kg")

        st.subheader("📋 Material-wise Stock Report")

        st.dataframe(
            stock,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("📊 Available Stock by Material")

        st.bar_chart(
            stock.set_index("Material")["Available Stock (kg)"]
        )

        if (stock["Available Stock (kg)"] < 0).any():
            st.warning(
                "काही material ची विक्री नोंद खरेदीपेक्षा जास्त आहे. "
                "नोंदी तपासा."
            )

        csv_stock = stock.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Stock Report",
            data=csv_stock,
            file_name="smartrecycle_stock_report.csv",
            mime="text/csv"
        )


# DASHBOARD
else:
    st.header("📊 Business Overview")

    transactions = load_transactions()
    prices = load_prices()

    if transactions.empty:
        purchase_total = 0.0
        sales_total = 0.0
        purchase_kg = 0.0
        sales_kg = 0.0
    else:
        purchases = transactions[
            transactions["transaction_type"] == "Purchase"
        ]

        sales = transactions[
            transactions["transaction_type"] == "Sale"
        ]

        purchase_total = purchases["total"].sum()
        sales_total = sales["total"].sum()
        purchase_kg = purchases["quantity"].sum()
        sales_kg = sales["quantity"].sum()

    difference = sales_total - purchase_total

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Purchase Cost", f"₹{purchase_total:,.2f}")
    c2.metric("Sales Revenue", f"₹{sales_total:,.2f}")
    c3.metric("Sales - Purchases", f"₹{difference:,.2f}")
    c4.metric(
        "Net Quantity Difference",
        f"{purchase_kg - sales_kg:,.1f} kg"
    )

    st.caption(
        "Sales - Purchases हा प्राथमिक आर्थिक फरक आहे; "
        "तो अचूक नफा नाही. Stock, इतर खर्च आणि material ची "
        "खर्चानुसार विक्री यात मोजलेली नाही."
    )

    st.divider()

    st.subheader("📦 Material-wise Purchase and Sale")

    if transactions.empty:
        st.info("Analysis पाहण्यासाठी आधी transactions सेव्ह करा.")
    else:
        material_summary = transactions.pivot_table(
            index="material",
            columns="transaction_type",
            values="total",
            aggfunc="sum",
            fill_value=0
        )

        for column in ["Purchase", "Sale"]:
            if column not in material_summary.columns:
                material_summary[column] = 0

        material_summary = material_summary[["Purchase", "Sale"]]

        st.bar_chart(material_summary)

        st.dataframe(
            material_summary.reset_index(),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("⚖️ Material-wise Quantity")

    if not transactions.empty:
        quantity_summary = transactions.pivot_table(
            index="material",
            columns="transaction_type",
            values="quantity",
            aggfunc="sum",
            fill_value=0
        )

        for column in ["Purchase", "Sale"]:
            if column not in quantity_summary.columns:
                quantity_summary[column] = 0

        quantity_summary["Difference (kg)"] = (
            quantity_summary["Purchase"] - quantity_summary["Sale"]
        )

        st.dataframe(
            quantity_summary.reset_index(),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("🧾 Recent Transactions")

    if transactions.empty:
        st.write("No records yet.")
    else:
        st.dataframe(
            transactions.head(10),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("🌐 Recent Market Prices")

    if prices.empty:
        st.info("Market prices अजून सेव्ह केलेले नाहीत.")
    else:
        st.dataframe(
            prices.head(10),
            use_container_width=True,
            hide_index=True
        )

        latest_prices = (
            prices.sort_values("price_date")
            .groupby("material", as_index=False)
            .tail(1)
            .sort_values("material")
        )

        st.subheader("Latest Saved Rate by Material")

        st.bar_chart(
            latest_prices.set_index("material")["rate"]
        )


st.divider()
st.caption("SmartRecycle AI | SQLite Database | Business Analytics")
