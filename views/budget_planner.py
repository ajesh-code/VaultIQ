import streamlit as st
from database.db_manager import DBManager

db = DBManager()

def show_budget_planner(user_id):
    st.title("Budgets")
    
    # Get dynamic categories
    category_options = db.get_or_create_user_categories(user_id)
    
    # --- Category Creation Header ---
    with st.expander("🛠️ Manage Your Categories", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            new_cat_name = st.text_input("New category name", placeholder="e.g. Subscriptions")
        with c2:
            st.markdown('<div style="margin-top: 1.7rem;"></div>', unsafe_allow_html=True)
            if st.button("Create Category", use_container_width=True):
                if new_cat_name:
                    if db.add_category(user_id, new_cat_name):
                        st.success(f"Added {new_cat_name}")
                        st.rerun()
                    else:
                        st.error("Already exists")

    # --- Set/Update Budget Section ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Set Allocation")
    b1, b2, b3 = st.columns([2, 2, 1])
    with b1:
        cat_to_budget = st.selectbox("Category", category_options)
    with b2:
        budget_amt = st.number_input("Limit (₹)", min_value=0.0, step=500.0)
    with b3:
        st.markdown('<div style="margin-top: 1.7rem;"></div>', unsafe_allow_html=True)
        if st.button("Set Budget", use_container_width=True):
            db.set_budget(user_id, cat_to_budget, budget_amt)
            st.toast(f"Budget updated for {cat_to_budget}", icon="🎯")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Budget Status Display ---
    st.subheader("Your Progress")
    
    budgets_df = db.get_budgets(user_id)
    transactions_df = db.get_transactions(user_id)
    
    if budgets_df.empty:
        st.markdown('''
            <div style="text-align: center; padding: 3rem;">
                <h1 style="font-size: 5rem; margin: 0;">🎯</h1>
                <h3>No budgets set</h3>
                <p class="text-dim">Assign limits to categories above to start tracking your discipline.</p>
            </div>
        ''', unsafe_allow_html=True)
        return

    # Render Budget Cards in a Grid
    cols = st.columns(2)
    for i, (_, row) in enumerate(budgets_df.iterrows()):
        cat = row['category']
        limit = row['amount']
        
        # Calculate current spend
        if not transactions_df.empty:
            actual = transactions_df[(transactions_df['category'] == cat) & (transactions_df['type'] == 'Expense')]['amount'].sum()
        else:
            actual = 0
            
        remaining = limit - actual
        perc = (actual / limit * 100) if limit > 0 else 0
        
        with cols[i % 2]:
            st.markdown(f'''
                <div class="glass-card" style="margin-bottom: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h4 style="margin: 0; font-weight: 600;">{cat}</h4>
                        <span class="text-dim">{perc:.1f}% Used</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-weight: bold; color: {'#ff3b30' if actual > limit else '#ffffff'}">₹{actual:,.0f}</span>
                        <span class="text-dim">Limit: ₹{limit:,.0f}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            
            # Progress bar color logic
            if actual > limit:
                st.progress(1.0)
                st.error(f"⚠️ Overspent by ₹{abs(remaining):,.0f}!")
            else:
                st.progress(min(actual/limit, 1.0) if limit > 0 else 0)
                if remaining > 0:
                    st.write(f"Remaining: **₹{remaining:,.0f}**")
                else:
                    st.write("**Budget Maxed Out**")
            
            st.markdown('<div style="margin-bottom: 2rem;"></div>', unsafe_allow_html=True)
