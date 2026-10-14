
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from supabase import create_client

st.set_page_config(
    page_title="SmartRecycle AI",
    page_icon="♻️",
    layout="wide",
)

MATERIALS = [
    "Plastic", "Paper", "Metal", "Glass",
    "Copper", "Aluminium", "Iron", "PET Bottles", "Other"
]

# Connect to Supabase using Streamlit secrets
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def fetch_table(table, order_column):
    response = (
        get_supabase()
        .table(table)
        .select("*")
        .order(order_column, desc=True)
        .execute()
    )
    return pd.DataFrame(response.data)


def load_transactions():
    df = fetch_table("transactions", "entry_date")
    if not df.empty:
        df = df.sort_values(
            ["entry_date", "id"], ascending=[False, False]
        )
    return df


def load_prices():
    df = fetch_table("market_prices", "price_date")
    if not df.empty:
        df = df.sort_values(
            ["price_date", "id"], ascending=[False, False]
        )
    return df


def excel_report(sheets):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])
    return output.getvalue()


def download_reports(dataframe, filename, sheet_name):
    csv_data = dataframe.to_csv(index=False).encode("utf-8-sig")
    excel_data = excel_report({sheet_name: dataframe})

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download CSV",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv",
            key=f"{filename}_csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "📊 Download Excel",
            data=excel_data,
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{filename}_excel",
            use_container_width=True,
        )


def money(value):
    return f"₹{float(value):,.2f}"


# Connect and load data
try:
    supabase = get_supabase()
    transactions = load_transactions()
    prices = load_prices()
except Exception as exc:
    st.error("Supabase connection किंवा database access मध्ये समस्या आहे.")
    st.info(
        "secrets.toml मधील URL आणि key तपासा. "
        "Supabase मध्ये RLS policies देखील तपासा."
    )
    st.caption(f"Technical details: {exc}")
    st.stop()


st.title("♻️ SmartRecycle AI")
st.caption("Recycling Business Intelligence Dashboard")
st.divider()

with st.sidebar:
    st.title("♻️ SmartRecycle")
    st.caption("Business Control Center")
    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Add Purchase / Sale",
            "Transaction History",
            "Market Prices",
            "Stock Management",
        ],
    )
    st.divider()
    st.caption("Track • Analyse • Recycle")


# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.header("📊 Business Overview")
    st.caption("Summary of your recorded recycling business activity.")

    if transactions.empty:
        purchase_total = sales_total = 0.0
        purchase_kg = sales_kg = 0.0
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

    available_stock = purchase_kg - sales_kg
    financial_difference = sales_total - purchase_total

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛒 Purchase Cost", money(purchase_total))
    c2.metric("💰 Sales Revenue", money(sales_total))
    c3.metric("📦 Available Quantity", f"{available_stock:,.1f} kg")
    c4.metric("🧾 Transactions", f"{len(transactions):,}")

    st.info(
        f"Sales Revenue − Purchase Cost: {money(financial_difference)}. "
        "हा प्राथमिक फरक आहे, अचूक नफा नाही; इतर खर्च आणि "
        "विकलेल्या मालाचा प्रत्यक्ष खर्च यात समाविष्ट नाही."
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Purchase vs Sales")
        if transactions.empty:
            st.info("Chart पाहण्यासाठी आधी transaction नोंदवा.")
        else:
            summary = transactions.pivot_table(
                index="material",
                columns="transaction_type",
                values="total",
                aggfunc="sum",
                fill_value=0,
            )
            for col in ["Purchase", "Sale"]:
                if col not in summary.columns:
                    summary[col] = 0
            st.bar_chart(summary[["Purchase", "Sale"]])

    with right:
        st.subheader("Stock by Material")
        if transactions.empty:
            st.info("Stock chart साठी आधी transactions नोंदवा.")
        else:
            stock_qty = transactions.pivot_table(
                index="material",
                columns="transaction_type",
                values="quantity",
                aggfunc="sum",
                fill_value=0,
            )
            for col in ["Purchase", "Sale"]:
                if col not in stock_qty.columns:
                    stock_qty[col] = 0
            stock_qty["Available Stock (kg)"] = (
                stock_qty["Purchase"] - stock_qty["Sale"]
            )
            st.bar_chart(stock_qty[["Available Stock (kg)"]])

    st.subheader("🧾 Recent Transactions")
    if transactions.empty:
        st.info("अजून transactions नोंदवलेले नाहीत.")
    else:
        st.dataframe(
            transactions.head(10),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("🌐 Latest Saved Market Prices")
    if prices.empty:
        st.info("Market prices अजून सेव्ह केलेले नाहीत.")
    else:
        latest = (
            prices.sort_values(["price_date", "id"])
            .groupby("material", as_index=False)
            .tail(1)
            .sort_values("material")
        )
        st.dataframe(latest, use_container_width=True, hide_index=True)


# ---------------- ADD TRANSACTION ----------------
elif page == "Add Purchase / Sale":
    st.header("📝 Add Business Transaction")

    with st.form("transaction_form", clear_on_submit=True):
        entry_date = st.date_input("Transaction Date", value=date.today())
        transaction_type = st.selectbox(
            "Transaction Type", ["Purchase", "Sale"]
        )
        material = st.selectbox("Material", MATERIALS)
        quantity = st.number_input(
            "Quantity (kg)", min_value=0.1, value=10.0, step=0.5
        )
        rate = st.number_input(
            "Rate (₹ per kg)", min_value=0.0, value=10.0, step=1.0
        )
        st.write(f"**Transaction Total: {money(quantity * rate)}**")
        submitted = st.form_submit_button(
            "💾 Save Transaction", use_container_width=True
        )

    if submitted:
        try:
            supabase.table("transactions").insert({
                "entry_date": str(entry_date),
                "transaction_type": transaction_type,
                "material": material,
                "quantity": quantity,
                "rate": rate,
                "total": round(quantity * rate, 2),
            }).execute()
            st.success(
                f"{transaction_type} saved successfully. "
                f"Total: {money(quantity * rate)}"
            )
            st.rerun()
        except Exception as exc:
            st.error("Transaction सेव्ह झाला नाही.")
            st.caption(f"Technical details: {exc}")


# ---------------- TRANSACTION HISTORY ----------------
elif page == "Transaction History":
    st.header("📚 Transaction History")

    if transactions.empty:
        st.info("No transactions saved yet.")
    else:
        date_col, type_col, material_col = st.columns(3)

        with date_col:
            start_date = st.date_input(
                "From Date",
                value=pd.to_datetime(
                    transactions["entry_date"]
                ).min().date(),
                key="history_start",
            )

        with type_col:
            end_date = st.date_input(
                "To Date", value=date.today(), key="history_end"
            )

        with material_col:
            type_filter = st.selectbox(
                "Type Filter", ["All", "Purchase", "Sale"]
            )

        filtered = transactions.copy()
        filtered["entry_date"] = pd.to_datetime(
            filtered["entry_date"], errors="coerce"
        ).dt.date

        if start_date > end_date:
            st.error("From Date ही To Date पेक्षा आधीची असावी.")
        else:
            filtered = filtered[
                (filtered["entry_date"] >= start_date)
                & (filtered["entry_date"] <= end_date)
            ]

            if type_filter != "All":
                filtered = filtered[
                    filtered["transaction_type"] == type_filter
                ]

            st.metric("Filtered Transactions", len(filtered))
            st.dataframe(
                filtered, use_container_width=True, hide_index=True
            )
            download_reports(
                filtered, "smartrecycle_transactions", "Transactions"
            )


# ---------------- MARKET PRICES ----------------
elif page == "Market Prices":
    st.header("🌐 Scrap Market Price Tracker")
    st.write(
        "वेबसाइटवर प्रकाशित दर तपासा आणि तारीख, material, दर व स्रोत सेव्ह करा."
    )
    st.markdown(
        "[Recyclo India](https://www.recycloindia.com/) · "
        "[Scrapprice Material List](https://www.scrapprice.in/scrap-materials)"
    )
    st.warning(
        "दर आपोआप website वरून घेतले जात नाहीत. प्रकाशित दर तपासून "
        "स्वतः नोंदवा; source link सुद्धा सेव्ह करा."
    )

    with st.form("market_form", clear_on_submit=True):
        price_date = st.date_input("Price Checked On", value=date.today())
        market_material = st.selectbox(
            "Material", MATERIALS, key="market_material"
        )
        market_rate = st.number_input(
            "Market Rate (₹ per kg)", min_value=0.0, value=0.0
        )
        source = st.text_input(
            "Source Website URL", placeholder="https://example.com/price"
        )
        save_price = st.form_submit_button(
            "💾 Save Market Price", use_container_width=True
        )

    if save_price:
        if market_rate <= 0:
            st.error("Market rate शून्यापेक्षा जास्त असावा.")
        elif not source.strip().startswith(("https://", "http://")):
            st.error("Valid source URL http:// किंवा https:// ने सुरू करा.")
        else:
            try:
                supabase.table("market_prices").insert({
                    "price_date": str(price_date),
                    "material": market_material,
                    "rate": market_rate,
                    "source": source.strip(),
                }).execute()
                st.success("Market price saved successfully!")
                st.rerun()
            except Exception as exc:
                st.error("Market price सेव्ह झाला नाही.")
                st.caption(f"Technical details: {exc}")

    st.subheader("📋 Saved Market Prices")
    if prices.empty:
        st.info("Market prices अजून सेव्ह केलेले नाहीत.")
    else:
        st.dataframe(prices, use_container_width=True, hide_index=True)

        st.subheader("📈 Market Price Trend")
        trend = prices.pivot_table(
            index="price_date",
            columns="material",
            values="rate",
            aggfunc="mean",
        ).sort_index()
        st.line_chart(trend)

        download_reports(
            prices, "smartrecycle_market_prices", "Market Prices"
        )


# ---------------- STOCK MANAGEMENT ----------------
elif page == "Stock Management":
    st.header("📦 Stock Management")

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
            "Total Sold (kg)": sales_qty,
        }).fillna(0)

        stock["Available Stock (kg)"] = (
            stock["Total Purchased (kg)"] - stock["Total Sold (kg)"]
        )
        stock = stock.reset_index().rename(
            columns={"material": "Material"}
        )

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Total Purchased",
            f"{stock['Total Purchased (kg)'].sum():,.1f} kg",
        )
        c2.metric(
            "Total Sold",
            f"{stock['Total Sold (kg)'].sum():,.1f} kg",
        )
        c3.metric(
            "Available Stock",
            f"{stock['Available Stock (kg)'].sum():,.1f} kg",
        )

        if (stock["Available Stock (kg)"] < 0).any():
            st.warning(
                "काही material ची विक्री नोंद खरेदीपेक्षा जास्त आहे. "
                "Stock आणि transaction नोंदी तपासा."
            )

        st.subheader("📋 Material-wise Stock Report")
        st.dataframe(stock, use_container_width=True, hide_index=True)

        st.subheader("📊 Available Stock by Material")
        st.bar_chart(
            stock.set_index("Material")[["Available Stock (kg)"]]
        )

        download_reports(
            stock, "smartrecycle_stock_report", "Stock Report"
        )


st.divider()
st.caption(
    "SmartRecycle AI • Recycling Business Intelligence • "
    "Supabase Database • CSV & Excel Reports"
)
