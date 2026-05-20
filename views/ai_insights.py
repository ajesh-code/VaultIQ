import streamlit as st
from database.db_manager import DBManager
import pandas as pd
import plotly.graph_objects as go

db = DBManager()

def show_ai_insights(user_id):
    st.title("Intelligent Insights")
    
    df = db.get_transactions(user_id)
    budgets = db.get_budgets(user_id)
    
    if df.empty:
        st.markdown('''
            <div style="text-align: center; padding: 3rem;">
                <h1 style="font-size: 5rem; margin: 0;">🧠</h1>
                <h3>AI needs data to think</h3>
                <p class="text-dim">Log a few transactions so we can analyze your spending habits.</p>
            </div>
        ''', unsafe_allow_html=True)
        return

    # --- Calculations ---
    df['date'] = pd.to_datetime(df['date'])
    income = df[df['type'] == 'Income']['amount'].sum()
    expenses = df[df['type'] == 'Expense']['amount'].sum()
    savings_rate = ((income - expenses) / income * 100) if income > 0 else 0

    # --- Financial Health Score Card ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([1, 2])
    
    with h_col1:
        # Gauge Chart for Health Score
        score = 0
        if savings_rate > 30: score = 95
        elif savings_rate > 20: score = 80
        elif savings_rate > 10: score = 60
        elif savings_rate > 0: score = 40
        else: score = 20

        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Health Score", 'font': {'size': 18, 'color': "white"}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#007aff"},
                'bgcolor': "rgba(255,255,255,0.05)",
                'borderwidth': 2,
                'bordercolor': "rgba(255,255,255,0.1)",
                'steps': [
                    {'range': [0, 40], 'color': 'rgba(255, 59, 48, 0.3)'},
                    {'range': [40, 70], 'color': 'rgba(255, 166, 77, 0.3)'},
                    {'range': [70, 100], 'color': 'rgba(52, 199, 89, 0.3)'}
                ],
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            font={'color': "white", 'family': "Plus Jakarta Sans"},
            margin=dict(t=0, b=0, l=20, r=20),
            height=200
        )
        st.plotly_chart(fig, use_container_width=True)

    with h_col2:
        st.subheader("Analysis Summary")
        st.write(f"Your monthly savings rate is **{savings_rate:.1f}%**.")
        if savings_rate > 20:
            st.success("🎯 **Elite Saver Streak!** You're maintaining a high savings rate. Keep it up for 3 months to unlock 'Wealth Builder' status.")
        else:
            st.warning("⚖️ **Balance Needed:** Your expenses are consuming most of your income. Aim for at least 20% savings to hit financial freedom faster.")
        st.write("---")
        st.write(f"💸 **Total Burn:** ₹{expenses:,.0f} | 💰 **Total In:** ₹{income:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Spending Behavior ---
    st.subheader("Behavioral Patterns")
    b_col1, b_col2 = st.columns(2)
    
    with b_col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write("#### 🏆 Top Category")
        expense_df = df[df['type'] == 'Expense']
        if not expense_df.empty:
            cat_totals = expense_df.groupby('category')['amount'].sum()
            top_cat = cat_totals.idxmax()
            top_val = cat_totals.max()
            st.markdown(f"<h1 style='margin:0; color:#007aff;'>{top_cat}</h1>", unsafe_allow_html=True)
            st.write(f"Total spent: ₹{top_val:,.0f}")
        else:
            st.write("No data yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with b_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write("#### 📅 Peak Activity")
        if not expense_df.empty:
            df['day'] = df['date'].dt.day_name()
            top_day = df[df['type'] == 'Expense'].groupby('day')['amount'].count().idxmax()
            st.markdown(f"<h1 style='margin:0; color:#5856d6;'>{top_day}</h1>", unsafe_allow_html=True)
            st.write("This is your most frequent spending day.")
        else:
            st.write("No data yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Personalized Recommendations ---
    st.subheader("Smart Recommendations")
    
    recs = []
    # 1. Budget overrun
    if not budgets.empty:
        expenses_by_cat = expense_df.groupby('category')['amount'].sum()
        for _, b in budgets.iterrows():
            actual = expenses_by_cat.get(b['category'], 0)
            if actual > b['amount']:
                recs.append(("🚨", f"Over budget in {b['category']}", f"You've exceeded your ₹{b['amount']:,.0f} limit. Consider trimming costs here next month."))
    
    # 2. Savings rule
    if income > 0 and (income - expenses) < income * 0.1:
        recs.append(("🔔", "Low Savings Alert", "You're saving less than 10%. Try the 50/30/20 rule to optimize your cash flow."))
    
    # 3. High single category
    if not expense_df.empty:
        cat_perc = (expense_df.groupby('category')['amount'].sum() / expenses * 100)
        for cat, perc in cat_perc.items():
            if perc > 40:
                recs.append(("📉", f"High {cat} Concentration", f"{cat} accounts for {perc:.0f}% of your spending. Check if there are cheaper alternatives."))

    if recs:
        for icon, title, text in recs:
            st.markdown(f'''
                <div class="glass-card" style="border-left: 4px solid #007aff;">
                    <h4 style="margin:0;">{icon} {title}</h4>
                    <p class="text-dim" style="margin: 5px 0 0 0;">{text}</p>
                </div>
            ''', unsafe_allow_html=True)
    else:
        st.success("✨ **Perfect Balance!** No critical warnings today. Your spending patterns are well within healthy limits.")
