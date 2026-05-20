import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database.db_manager import DBManager
import pandas as pd

db = DBManager()

def show_dashboard(user_id):
    st.title("Financial Overview")
    
    df = db.get_transactions(user_id)
    
    if df.empty:
        st.markdown('''
            <div style="text-align: center; padding: 4rem 2rem;">
                <h1 style="font-size: 5rem; margin-bottom: 1rem;">📈</h1>
                <h2>No data to visualize yet</h2>
                <p class="text-dim">Log your income and expenses in the Transactions page to see your financial trends and allocation.</p>
            </div>
        ''', unsafe_allow_html=True)
        return

    # --- Calculation Engine ---
    df['date'] = pd.to_datetime(df['date'])
    income = df[df['type'] == 'Income']['amount'].sum()
    expenses = df[df['type'] == 'Expense']['amount'].sum()
    balance = income - expenses
    savings_rate = ((income - expenses) / income * 100) if income > 0 else 0

    # --- Top Row: Premium Summary Cards ---
    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    with m_col1:
        st.markdown(f'''
            <div class="glass-card">
                <p class="text-dim" style="text-transform: uppercase; font-size: 0.75rem; font-weight: 600;">Total Balance</p>
                <h2 style="margin: 0; color: #007aff;">₹{balance:,.0f}</h2>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_col2:
        st.markdown(f'''
            <div class="glass-card">
                <p class="text-dim" style="text-transform: uppercase; font-size: 0.75rem; font-weight: 600;">Income</p>
                <h2 style="margin: 0; color: #34c759;">₹{income:,.0f}</h2>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_col3:
        st.markdown(f'''
            <div class="glass-card">
                <p class="text-dim" style="text-transform: uppercase; font-size: 0.75rem; font-weight: 600;">Expenses</p>
                <h2 style="margin: 0; color: #ff3b30;">₹{expenses:,.0f}</h2>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_col4:
        st.markdown(f'''
            <div class="glass-card">
                <p class="text-dim" style="text-transform: uppercase; font-size: 0.75rem; font-weight: 600;">Savings Rate</p>
                <h2 style="margin: 0; color: #5856d6;">{savings_rate:.1f}%</h2>
            </div>
        ''', unsafe_allow_html=True)

    # --- Middle Row: Charts ---
    c_col1, c_col2 = st.columns([1.6, 1])
    
    with c_col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Monthly Comparison")
        
        # Prepare trend data
        trend_df = df.groupby([pd.Grouper(key='date', freq='ME'), 'type'])['amount'].sum().unstack(fill_value=0).reset_index()
        
        if not trend_df.empty:
            fig = go.Figure()
            if 'Income' in trend_df.columns:
                fig.add_trace(go.Bar(
                    x=trend_df['date'], y=trend_df['Income'], 
                    name='Income', marker_color='#34c759'
                ))
            if 'Expense' in trend_df.columns:
                fig.add_trace(go.Bar(
                    x=trend_df['date'], y=trend_df['Expense'], 
                    name='Expense', marker_color='#ff3b30'
                ))
            
            fig.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white", family="Plus Jakarta Sans"),
                xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Amount (₹)"),
                margin=dict(t=20, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_traces(hovertemplate="₹%{y:,.0f}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Insufficient data for comparison.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Allocation")
        expense_df = df[df['type'] == 'Expense']
        if not expense_df.empty:
            cat_df = expense_df.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(
                cat_df, values='amount', names='category', 
                hole=0.6,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig.update_traces(textinfo='none', hovertemplate="%{label}: ₹%{value:,.0f}")
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white", family="Plus Jakarta Sans"),
                margin=dict(t=10, b=0, l=0, r=0),
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=0, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<p style="padding: 2rem 0; text-align: center;" class="text-dim">No expenses to display yet.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Insight Section ---
    st.markdown('<div class="glass-card" style="padding: 1.5rem 2rem;">', unsafe_allow_html=True)
    st.subheader("Smart Insights")
    i_col1, i_col2 = st.columns(2)
    
    with i_col1:
        if not expense_df.empty:
            top_cat = expense_df.groupby('category')['amount'].sum().idxmax()
            st.markdown(f"🔥 Your highest spending is in **{top_cat}** category.")
        else:
            st.write("✨ Keep tracking to unlock spending insights.")
            
    with i_col2:
        if balance > 0:
            st.markdown(f"✅ You have a positive cash flow of **₹{balance:,.0f}**. Consider investing!")
        elif balance < 0:
            st.markdown(f"⚠️ You've spent **₹{abs(balance):,.0f}** more than your income. Review your budgets!")
    st.markdown('</div>', unsafe_allow_html=True)
