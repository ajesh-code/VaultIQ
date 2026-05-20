# 💰 Premium Expense Tracker

Welcome to your startup-level financial management suite! This app is built with **Streamlit**, **SQLite**, and **Plotly** to provide a beautiful, data-driven experience.

## 🚀 Getting Started

### 1. Installation
The app automatically installs its dependencies from `requirements.txt`. If you need to do it manually:
```bash
pip install -r requirements.txt
```

### 2. Run the App
Navigate to this folder and run:
```bash
streamlit run main.py
```

## 🏗️ Folder Structure (Modular Architecture)
- **`main.py`**: The "Heart" of the app. Handles navigation, styling, and login.
- **`assets/`**: Contains `style.css` for that modern **Glassmorphism** look (blur effects, gradients).
- **`database/`**: Contains `db_manager.py`, which talks to the SQLite database. It handles your users, transactions, and budgets.
- **`pages/`**:
    - `dashboard.py`: Your financial command center with Plotly charts.
    - `transactions.py`: Where you add, search, and delete records.
    - `ai_insights.py`: Rule-based logic that gives you financial advice and alerts.
    - `budget_planner.py`: Set your goals and limits.

## 🤖 AI Features (Simulated)
This version uses "Rule-Based AI". It analyzes your data using smart logic:
- **Overspending Alerts**: Compares your actual spending vs. the budgets you set.
- **Savings Recommendations**: Identifies high spending in discretionary categories (like Dining).
- **Financial Health Score**: A dynamic score based on your savings rate.

## 💡 Pro Tips for Beginners
- **SQLite**: No setup required! It creates a local `.db` file in the `database/` folder.
- **Pandas**: We use this to turn database rows into "DataFrames" for easy math and charting.
- **Streamlit**: Every time you change code, the app refreshes automatically!

---
Enjoy your journey to financial freedom! 💸
