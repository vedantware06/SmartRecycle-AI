# ♻️ SmartRecycle AI
### AI-Based Recycling Business Intelligence & Stock Management System

SmartRecycle AI is a Python-based web application designed to help recycling and scrap businesses manage purchase and sales transactions, track material stock, monitor scrap market prices, and view business analytics through an interactive dashboard.

## 📌 Project Overview

The project provides a centralized dashboard for recording business transactions and analyzing material-wise quantities, purchase costs, sales revenue, stock availability, and saved market price records.

## ✨ Features

- 📊 **Business Dashboard** — View purchase costs, sales revenue, and quantity differences.
- 📝 **Purchase and Sales Management** — Record material, date, quantity, and rate.
- 📚 **Transaction History** — View saved transactions and export them to CSV.
- 🌐 **Scrap Market Price Tracker** — Save manually checked market rates with their source URLs.
- 📦 **Stock Management** — Calculate available stock by material using recorded purchases and sales.
- 📈 **Interactive Charts** — Visualize material-wise transactions and stock.
- 💾 **SQLite Database** — Store business transactions and market price records locally.
- 📥 **CSV Reports** — Export transaction, market price, and stock reports.

## 🛠️ Technologies Used

- Python
- Streamlit
- Pandas
- SQLite
- Data Visualization
- Git and GitHub

## 🖥️ Application Modules

1. Dashboard
2. Add Purchase / Sale
3. Transaction History
4. Market Prices
5. Stock Management

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/vedantware06/SmartRecycle-AI.git
cd SmartRecycle-AI
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
streamlit run app.py
```

The application will open in your browser, usually at `http://localhost:8501`.

## 🗄️ Database

The application uses SQLite to store purchase and sale transactions and manually entered market price records. The database file is created locally when the application runs.

## ⚠️ Current Limitations

- Market prices are entered manually; automatic live price fetching is not implemented.
- Stock is calculated from recorded purchase and sale quantities.
- The current sales-minus-purchases figure is a basic financial difference, not an exact net profit calculation.
- Machine learning-based forecasting is not yet implemented.

## 🚀 Future Enhancements

- Automated market price integration from reliable data sources
- More accurate material-wise profit and loss analysis
- Stock alerts and low-stock notifications
- AI/ML-based scrap price forecasting
- Improved analytics and reporting

## 👨‍💻 Author

**Vedant Ajay Ware**

Project: SmartRecycle AI  
Domain: Recycling Business Intelligence and Data Analytics