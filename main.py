"""
Main application entry point
Modular Smart Face Attendance System
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize basic logging first
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Import configuration and core components
    from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT, SIDEBAR_STATE
    from config.logging_config import setup_logging
    from database.connection import init_database
    from auth.session_manager import SessionManager
    from ui.pages.login_page import LoginPage
    from ui.pages.dashboard_page import DashboardPage
    from ui.components.theme_toggle import apply_theme  # Add theme import
    
    # Set up proper logging
    logger = setup_logging()
    
except ImportError as e:
    st.error(f"❌ Import Error: {str(e)}")
    st.error("🔧 Please ensure all required files are in place")
    st.stop()

# Streamlit configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE
)

def load_custom_css():
    """Load custom CSS styling"""
    try:
        css_file = project_root / "static" / "styles.css"
        if css_file.exists():
            with open(css_file, "r") as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        else:
            logger.warning("CSS file not found. Using default styling.")
    except Exception as e:
        logger.error(f"Error loading CSS: {e}")

def initialize_application():
    """Initialize application components"""
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized successfully")
        
        # Load custom styling
        load_custom_css()
        
        # Apply theme (NEW)
        current_theme = apply_theme()
        logger.info(f"Applied {current_theme} theme")
        
        return True
        
    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        st.error(f"❌ Application initialization failed: {str(e)}")
        return False

def main():
    """Main application logic"""
    # Show loading message
    with st.spinner("🚀 Initializing Smart Face Attendance System..."):
        # Initialize application
        if not initialize_application():
            st.error("Failed to initialize application. Please check the error details above.")
            return
    
    # Initialize session manager
    try:
        session_manager = SessionManager()
    except Exception as e:
        st.error(f"❌ Session management error: {str(e)}")
        logger.error(f"Session manager error: {e}")
        return
    
    # Route to appropriate page based on authentication status
    try:
        if session_manager.is_authenticated():
            # User is logged in - show dashboard
            dashboard = DashboardPage()
            dashboard.render()
        else:
            # User not logged in - show login page
            login_page = LoginPage()
            login_page.render()
            
    except Exception as e:
        logger.error(f"Application runtime error: {e}")
        st.error("❌ An unexpected error occurred.")
        
        # Show error details in expander for debugging
        with st.expander("🔧 Error Details"):
            st.exception(e)
        
        # Provide recovery options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reload Page", use_container_width=True, key="main_reload"):
                st.rerun()
        
        with col2:
            if st.button("🚪 Clear Session", use_container_width=True, key="main_clear_session"):
                try:
                    session_manager.logout_user()
                    st.rerun()
                except:
                    # If session manager fails, clear session state manually
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.critical(f"Critical application error: {e}")
        st.error("💥 Critical application error. Please restart the application.")
        if st.checkbox("🔧 Show Debug Info"):
            st.exception(e)
