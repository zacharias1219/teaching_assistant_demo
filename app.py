import streamlit as st
from dotenv import load_dotenv
from utils.auth import auth_manager
from datetime import timedelta

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Teacher's Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b35;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-pending {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

def main():
    """Main application entry point"""
    
    # Show login if not authenticated
    if not st.session_state.authenticated:
        show_login()
    else:
        # Show appropriate dashboard based on role
        if st.session_state.user_role == 'admin':
            show_admin_navigation()
        elif st.session_state.user_role == 'student':
            show_student_navigation()

def show_login():
    """Display login form"""
    st.title("🎓 Teacher's Assistant")
    st.markdown("### Please log in to continue")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if authenticate_user(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user credentials using the auth manager"""
    try:
        # Check if user is locked out
        if auth_manager.is_locked_out(username):
            remaining_time = auth_manager.get_lockout_time_remaining(username)
            if remaining_time:
                minutes = int(remaining_time.total_seconds() / 60)
                seconds = int(remaining_time.total_seconds() % 60)
                st.error(f"Account locked. Try again in {minutes}m {seconds}s")
            return False
        
        # Attempt authentication
        user_data = auth_manager.authenticate_user(username, password)
        
        if user_data:
            st.session_state.authenticated = True
            st.session_state.user_role = user_data["role"]
            st.session_state.username = user_data["username"]
            st.session_state.user_id = user_data["user_id"]
            return True
        else:
            # Check if now locked out after this attempt
            if auth_manager.is_locked_out(username):
                st.error(f"Too many failed attempts. Account locked for 5 minutes.")
            else:
                attempts_left = auth_manager.max_attempts - len(auth_manager.failed_attempts.get(username, []))
                st.error(f"Invalid credentials. {attempts_left} attempts remaining.")
            return False
            
    except Exception as e:
        st.error("Authentication error. Please try again.")
        print(f"Auth error: {e}")
        return False

def show_admin_navigation():
    """Show navigation for admin users"""
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.markdown("**Admin Dashboard**")
    
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
    
    # Import and show admin dashboard
    from components.admin_dashboard import admin_dashboard
    admin_dashboard()

def show_student_navigation():
    """Show navigation for student users"""
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.markdown("**Student Dashboard**")
    
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
    
    # Import and show student dashboard
    from components.student_dashboard import show_student_dashboard
    show_student_dashboard()

def logout():
    """Clear session and logout user"""
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.session_state.user_id = None
    st.rerun()

if __name__ == "__main__":
    main()
