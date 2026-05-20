import streamlit as st
import pandas as pd
from database.db_manager import DBManager
from utils.helpers import get_display_id

db = DBManager()

def show_trash_bin(user_id):
    st.title("🗑️ Trash Bin")
    st.markdown('<p class="text-dim">Review and manage your recently deleted transactions. Items here do not impact your dashboard or budgets.</p>', unsafe_allow_html=True)
    
    # Fetch soft-deleted transactions
    df_deleted = db.get_transactions(user_id, include_deleted=True)
    
    if not df_deleted.empty:
        # Prepare display
        display_df = df_deleted.copy()
        display_df['Display ID'] = display_df['id'].apply(get_display_id)
        display_df['amount_fmt'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
        
        # UI Table
        st.markdown('<div class="glass-card" style="border-left: 4px solid #ff3b30;">', unsafe_allow_html=True)
        cols_to_show = ['Display ID', 'deleted_at', 'category', 'amount_fmt', 'description']
        st.dataframe(
            display_df[cols_to_show].rename(columns={'amount_fmt': 'Amount', 'deleted_at': 'Deleted On'}), 
            use_container_width=True, 
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Management Actions
        st.markdown("### ⚡ Recovery Actions")
        
        # Map for selection
        txn_map = {get_display_id(row['id']): row['id'] for _, row in df_deleted.iterrows()}
        
        col_select, col_restore, col_hard_delete = st.columns([2, 1, 1])
        
        with col_select:
            selected_display_id = st.selectbox("Select Transaction to Manage", list(txn_map.keys()), label_visibility="collapsed")
        
        actual_id = txn_map[selected_display_id]
        
        with col_restore:
            if st.button("🔄 Restore", use_container_width=True):
                db.restore_transaction(actual_id, user_id)
                st.toast(f"Restored {selected_display_id}!", icon="✅")
                st.rerun()
                
        with col_hard_delete:
            if st.button("🔥 Purge", use_container_width=True):
                st.session_state.confirm_hard_delete = actual_id
                
        if 'confirm_hard_delete' in st.session_state and st.session_state.confirm_hard_delete == actual_id:
            st.markdown(f'''
                <div class="glass-card" style="border: 1px solid #ff3b30; background: rgba(255, 59, 48, 0.1);">
                    <p style="color: #ff3b30; font-weight: bold; margin-bottom: 1rem;">
                        ⚠️ Are you sure? This will permanently erase {selected_display_id} and cannot be undone.
                    </p>
                </div>
            ''', unsafe_allow_html=True)
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                if st.button("Yes, Delete Permanently", type="primary", use_container_width=True):
                    db.hard_delete_transaction(actual_id, user_id)
                    st.toast(f"Permanently Deleted {selected_display_id}", icon="🔥")
                    del st.session_state.confirm_hard_delete
                    st.rerun()
            with col_conf2:
                if st.button("No, Keep it", use_container_width=True):
                    del st.session_state.confirm_hard_delete
                    st.rerun()
    else:
        st.markdown('''
            <div style="text-align: center; padding: 5rem;">
                <h1 style="font-size: 6rem; margin: 0; opacity: 0.5;">♻️</h1>
                <h3>Trash bin is clear</h3>
                <p class="text-dim">Deleted transactions will appear here for 30 days before automatic purge (simulated).</p>
            </div>
        ''', unsafe_allow_html=True)
