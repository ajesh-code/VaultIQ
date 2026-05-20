import streamlit as st
import os
from database.db_manager import DBManager

# Initialize Database Manager
db = DBManager()

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="VaultIQ | Intelligence in Finance",
        page_icon="💎",
        layout="wide",
        initial_sidebar_state="collapsed" if 'user_id' not in st.session_state or st.session_state.user_id is None else "expanded"
    )
    
    # Global Sidebar Hiding logic for Auth Page
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.markdown("""
            <style>
                [data-testid="stSidebar"] {display: none;}
                [data-testid="stSidebarNav"] {display: none;}
                [data-testid="stSidebarCollapsedControl"] {display: none;}
                .stApp { margin-left: 0px !important; }
            </style>
        """, unsafe_allow_html=True)

    # Load custom glassmorphism styling
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "assets", "style.css")
    if os.path.exists(css_path):
        load_css(css_path)

    # Authentication Session State
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None

    # --- Sidebar Navigation (Logged In Only) ---
    if st.session_state.user_id:
        st.sidebar.markdown('<h1 class="sidebar-logo">VaultIQ</h1>', unsafe_allow_html=True)
        st.sidebar.markdown(f'<p class="sidebar-user">Welcome, {st.session_state.username}</p>', unsafe_allow_html=True)
        
        page = st.sidebar.radio("Navigate", ["Dashboard", "Transactions", "Trash Bin", "AI Insights", "Budget Planner"], label_visibility="collapsed")
        
        st.sidebar.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

        # Route to pages
        try:
            if page == "Dashboard":
                from views.dashboard import show_dashboard
                show_dashboard(st.session_state.user_id)
            elif page == "Transactions":
                from views.transactions import show_transactions
                show_transactions(st.session_state.user_id)
            elif page == "Trash Bin":
                from views.trash_bin import show_trash_bin
                show_trash_bin(st.session_state.user_id)
            elif page == "AI Insights":
                from views.ai_insights import show_ai_insights
                show_ai_insights(st.session_state.user_id)
            elif page == "Budget Planner":
                from views.budget_planner import show_budget_planner
                show_budget_planner(st.session_state.user_id)
        except Exception as e:
            st.error(f"Error loading page: {e}")
            st.exception(e)
    else:
        # --- VaultIQ Premium Landing Page ---
        # 1. Mesh Gradient Background Layer (-3)
        st.markdown('<div class="hero-bg"></div>', unsafe_allow_html=True)
        
        # 2. tsParticles Layer (-2) using HTML Component for reliability
        st.components.v1.html(
            '''
            <div id="tsparticles" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -2;"></div>
            <script src="https://cdn.jsdelivr.net/npm/tsparticles@2.12.0/tsparticles.bundle.min.js"></script>
            <script>
                tsParticles.load("tsparticles", {
                    fullScreen: { enable: false },
                    particles: {
                        number: { value: 70, density: { enable: true, value_area: 800 } },
                        color: { value: ["#007aff", "#5856d6", "#00d4ff"] },
                        shape: { type: "circle" },
                        opacity: {
                            value: 0.6,
                            random: true,
                            anim: { enable: true, speed: 0.8, opacity_min: 0.2, sync: false }
                        },
                        size: {
                            value: 4,
                            random: true,
                            anim: { enable: true, speed: 2, size_min: 0.5, sync: false }
                        },
                        links: {
                            enable: true,
                            distance: 150,
                            color: "#007aff",
                            opacity: 0.3,
                            width: 1.5
                        },
                        move: {
                            enable: true,
                            speed: 1.2,
                            direction: "none",
                            random: false,
                            straight: false,
                            out_mode: "out",
                            bounce: false,
                        }
                    },
                    interactivity: {
                        events: {
                            onhover: { enable: true, mode: "grab" },
                            onclick: { enable: true, mode: "push" },
                            resize: true
                        },
                        modes: {
                            grab: { distance: 160, links: { opacity: 0.6 } },
                            push: { quantity: 4 }
                        }
                    },
                    retina_detect: true
                });
            </script>
            <style>
                body { margin: 0; overflow: hidden; background: transparent; }
            </style>
            ''',
            height=0, # Keep it invisible in the layout but let it render fullscreen
            width=0
        )
        
        # 3. Content Layer (1+)
        # Hero Content
        st.markdown('''
            <div class="hero-section">
                <div class="hero-badge">Next-Gen Wealth Management</div>
                <h1 class="hero-logo">Vault<span class="iq-accent">IQ</span></h1>
                <p class="hero-tagline">AI-powered finance tracking for modern wealth management.</p>
            </div>
        ''', unsafe_allow_html=True)

        # Centered Auth Card
        col_l, col_main, col_r = st.columns([1, 1.2, 1])
        
        with col_main:
            st.markdown('<div class="glass-card auth-card fade-in">', unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["Login", "Create Account"])
            
            with tab1:
                login_user = st.text_input("Username", key="login_user", placeholder="Enter your identity")
                login_pass = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
                st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
                if st.button("Enter Dashboard", use_container_width=True, type="primary"):
                    user_id = db.verify_user(login_user, login_pass)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = login_user
                        st.success(f"Identity Verified. Welcome back.")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                        
            with tab2:
                new_user = st.text_input("Choose Username", key="new_user", placeholder="e.g. Satoshi")
                new_pass = st.text_input("Set Password", type="password", key="new_pass", placeholder="Create a strong key")
                confirm_pass = st.text_input("Confirm Password", type="password", key="confirm_pass", placeholder="Repeat your key")
                st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
                if st.button("Initialize Vault", use_container_width=True):
                    if not new_user or not new_pass:
                        st.warning("Please provide all details")
                    elif new_pass != confirm_pass:
                        st.warning("Keys do not match")
                    elif db.create_user(new_user, new_pass):
                        st.success("Vault Initialized! Access your dashboard now.")
                    else:
                        st.error("Identity already exists")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Sub-Card Info
            st.markdown('''
                <div class="info-card">
                    <p>✨ <b>Tip:</b> VaultIQ uses advanced rule-based AI to categorize your spending patterns automatically.</p>
                </div>
            ''', unsafe_allow_html=True)
        
        # Footer
        st.markdown('<div class="premium-footer">Created by Ajesh V M</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
