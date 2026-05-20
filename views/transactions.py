import streamlit as st
import pandas as pd
from database.db_manager import DBManager
from datetime import datetime, date
from utils.helpers import get_display_id

db = DBManager()

def show_transactions(user_id):
    st.title("Transaction Management")
    
    # Get dynamic categories
    category_options = db.get_or_create_user_categories(user_id)
    if "Other" not in category_options:
        category_options.append("Other")

    # --- Session State for Editing ---
    if 'editing_id' not in st.session_state:
        st.session_state.editing_id = None
    if 'confirm_delete_id' not in st.session_state:
        st.session_state.confirm_delete_id = None

    # --- Header Actions (Tabs) ---
    tab_entry, tab_history, tab_manage = st.tabs(["➕ Add / Edit", "📜 History & Search", "⚙️ Categories"])
    
    with tab_entry:
        form_title = "Record New Transaction"
        button_label = "Save Transaction"
        
        initial_type = "Expense"
        initial_amount = 0.0
        initial_category = category_options[0]
        initial_date = date.today()
        initial_desc = ""

        if st.session_state.editing_id:
            form_title = f"Edit {get_display_id(st.session_state.editing_id)}"
            button_label = "Update Changes"
            # We fetch all transactions to find the one we're editing
            df_all = db.get_transactions(user_id)
            try:
                edit_row = df_all[df_all['id'] == st.session_state.editing_id].iloc[0]
                initial_type = edit_row['type']
                initial_amount = float(edit_row['amount'])
                initial_date = datetime.strptime(edit_row['date'], "%Y-%m-%d").date()
                initial_desc = edit_row['description'] or ""
                initial_category = edit_row['category'] if edit_row['category'] in category_options else "Other"
            except IndexError:
                st.session_state.editing_id = None

        st.markdown(f'### {form_title}')
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                t_type = st.selectbox("Type", ["Expense", "Income"], index=0 if initial_type == "Expense" else 1)
                amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, value=initial_amount)
                category = st.selectbox("Category", category_options, index=category_options.index(initial_category) if initial_category in category_options else 0)
                if category == "Other":
                    category = st.text_input("New Category Name")
            with col2:
                t_date = st.date_input("Date", initial_date)
                description = st.text_area("Memo / Description", value=initial_desc, placeholder="What was this for?", height=115)
                
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button(button_label, use_container_width=True, type="primary"):
                    if amount > 0 and category:
                        if st.session_state.editing_id:
                            db.update_transaction(st.session_state.editing_id, user_id, t_type, category, amount, t_date.strftime("%Y-%m-%d"), description)
                            st.toast("Transaction Updated!", icon="✅")
                            st.session_state.editing_id = None
                        else:
                            db.add_transaction(user_id, t_type, category, amount, t_date.strftime("%Y-%m-%d"), description)
                            st.toast("Transaction Recorded!", icon="💰")
                        st.rerun()
            with col_b2:
                if st.session_state.editing_id:
                    if st.button("Cancel Editing", use_container_width=True):
                        st.session_state.editing_id = None
                        st.rerun()

    with tab_history:
        df = db.get_transactions(user_id)
        if not df.empty:
            # Filters
            f1, f2, f3 = st.columns([2, 1, 1])
            with f1:
                search = st.text_input("🔍 Search description...", placeholder="Coffee, Rent, etc.")
            with f2:
                f_type = st.selectbox("Type", ["All", "Income", "Expense"])
            with f3:
                sort_by = st.selectbox("Sort", ["Newest", "Oldest", "Highest", "Lowest"])

            # Apply Logic
            filtered = df.copy()
            if search: filtered = filtered[filtered['description'].str.contains(search, case=False, na=False)]
            if f_type != "All": filtered = filtered[filtered['type'] == f_type]
            
            if sort_by == "Newest": filtered = filtered.sort_values('date', ascending=False)
            elif sort_by == "Oldest": filtered = filtered.sort_values('date', ascending=True)
            elif sort_by == "Highest": filtered = filtered.sort_values('amount', ascending=False)
            elif sort_by == "Lowest": filtered = filtered.sort_values('amount', ascending=True)

            # Display
            display_df = filtered.copy()
            display_df['ID'] = display_df['id'].apply(get_display_id)
            display_df['Amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
            
            cols = ['ID', 'date', 'type', 'category', 'Amount', 'description']
            st.dataframe(display_df[cols].rename(columns={'date': 'Date', 'type': 'Type', 'category': 'Category', 'description': 'Notes'}), use_container_width=True, hide_index=True)
            
            # Actions Section
            st.markdown("### ⚡ Manage Selection")
            txn_map = {get_display_id(row['id']): row['id'] for _, row in filtered.iterrows()}
            
            a1, a2, a3 = st.columns([2, 1, 1])
            with a1:
                sel_id = st.selectbox("Select Transaction", list(txn_map.keys()), label_visibility="collapsed")
                actual_id = txn_map[sel_id]
            
            with a2:
                if st.button("✏️ Edit", use_container_width=True):
                    st.session_state.editing_id = actual_id
                    st.toast(f"Editing {sel_id}")
                    st.rerun()
            
            with a3:
                if st.button("🗑️ Trash", use_container_width=True):
                    st.session_state.confirm_delete_id = actual_id

            if st.session_state.confirm_delete_id == actual_id:
                st.warning(f"Move {sel_id} to Trash Bin?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Confirm Move", type="primary", use_container_width=True):
                        db.delete_transaction(actual_id, user_id)
                        st.toast("Moved to Trash Bin", icon="🗑️")
                        if st.session_state.editing_id == actual_id:
                            st.session_state.editing_id = None
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                with c2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.confirm_delete_id = None
                        st.rerun()
        else:
            st.info("No transactions recorded yet. Head over to 'Add / Edit' to start!")

    with tab_manage:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Category Control")
        m_col1, m_col2 = st.columns(2)
        
        with m_col1:
            st.write("**Rename**")
            old_cat = st.selectbox("Select", [c for c in category_options if c != "Other"], key="rename_old")
            new_name = st.text_input("New Name", key="rename_new")
            if st.button("Rename Category", use_container_width=True):
                if new_name and db.rename_category(user_id, old_cat, new_name):
                    st.success(f"Renamed {old_cat} to {new_name}")
                    st.rerun()
        
        with m_col2:
            st.write("**Merge**")
            src_cat = st.selectbox("Source (Delete)", [c for c in category_options if c != "Other"], key="merge_src")
            target_cat = st.selectbox("Target (Keep)", [c for c in category_options if c != src_cat], key="merge_target")
            if st.button("Merge Categories", use_container_width=True):
                db.merge_categories(user_id, src_cat, target_cat)
                st.success(f"Merged {src_cat} into {target_cat}")
                st.rerun()
        
        st.write("---")
        st.write("**Danger Zone**")
        del_cat = st.selectbox("Delete Permanently", [c for c in category_options if c != "Other"], key="del_cat")
        if st.button("Remove Category", use_container_width=True):
            db.delete_category(user_id, del_cat)
            st.warning(f"Category '{del_cat}' removed. Transactions reassigned to 'Other'.")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
