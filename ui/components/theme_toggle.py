"""
Theme toggle component
Provides dark/light theme switching functionality
"""
import streamlit as st
from typing import Optional

class ThemeToggle:
    """Theme toggle component for dark/light mode switching"""
    
    def __init__(self):
        self.theme_key = 'app_theme'
        self.default_theme = 'light'
    
    def get_current_theme(self) -> str:
        """Get current theme from session state"""
        return st.session_state.get(self.theme_key, self.default_theme)
    
    def set_theme(self, theme: str):
        """Set current theme in session state"""
        st.session_state[self.theme_key] = theme
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        current = self.get_current_theme()
        new_theme = 'dark' if current == 'light' else 'light'
        self.set_theme(new_theme)
        st.rerun()
    
    def render_toggle_button(self, container=None) -> Optional[str]:
        """Render theme toggle button"""
        current_theme = self.get_current_theme()
        
        # Use provided container or default
        if container is None:
            container = st
        
        # Theme icons and text
        if current_theme == 'light':
            icon = "🌙"
            text = "Dark Mode"
            new_theme = 'dark'
        else:
            icon = "☀️"
            text = "Light Mode" 
            new_theme = 'light'
        
        # Render button
        if container.button(f"{icon} {text}", key="theme_toggle_btn", help="Toggle dark/light mode"):
            self.set_theme(new_theme)
            st.rerun()
        
        return current_theme
    
    def render_sidebar_toggle(self):
        """Render theme toggle in sidebar"""
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🎨 Theme")
            self.render_toggle_button()
    
    def render_header_toggle(self):
        """Render theme toggle in header area"""
        # Create a container at the top right
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col3:
            self.render_toggle_button()
    
    def apply_theme_css(self):
        """Apply theme-specific CSS"""
        current_theme = self.get_current_theme()
        
        if current_theme == 'dark':
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
    
    def _apply_dark_theme(self):
        """Apply dark theme CSS"""
        dark_css = """
        <style>
        /* Dark Theme Variables */
        :root {
            --bg-primary: #0f172a !important;
            --bg-secondary: #1e293b !important;
            --bg-tertiary: #334155 !important;
            --text-primary: #f8fafc !important;
            --text-secondary: #cbd5e1 !important;
            --text-muted: #94a3b8 !important;
            --border-color: #475569 !important;
        }
        
        /* Dark theme overrides */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%) !important;
            color: var(--text-primary) !important;
        }
        
        .main .block-container {
            background: rgba(15, 23, 42, 0.95) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-primary) !important;
        }
        
        /* Sidebar dark theme */
        .css-1d391kg {
            background: var(--bg-secondary) !important;
            border-right: 1px solid var(--border-color) !important;
        }
        
        /* Input fields dark theme */
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox > div > div > div {
            background: var(--bg-tertiary) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }
        
        /* Metrics dark theme */
        .metric-container {
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
        }
        
        /* Tables dark theme */
        .stDataFrame {
            background: var(--bg-secondary) !important;
        }
        
        /* Markdown text */
        .stMarkdown {
            color: var(--text-primary) !important;
        }
        
        /* Form elements */
        .stForm {
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border-color) !important;
        }
        
        /* File uploader dark theme */
        .stFileUploader {
            background: var(--bg-tertiary) !important;
            border-color: var(--border-color) !important;
        }
        </style>
        """
        
        st.markdown(dark_css, unsafe_allow_html=True)
    
    def _apply_light_theme(self):
        """Apply light theme CSS"""
        light_css = """
        <style>
        /* Light Theme Variables */
        :root {
            --bg-primary: #ffffff !important;
            --bg-secondary: #f8fafc !important;
            --bg-tertiary: #f1f5f9 !important;
            --text-primary: #0f172a !important;
            --text-secondary: #475569 !important;
            --text-muted: #64748b !important;
            --border-color: #e2e8f0 !important;
        }
        
        /* Light theme overrides */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: var(--text-primary) !important;
        }
        
        .main .block-container {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-primary) !important;
        }
        
        /* Sidebar light theme */
        .css-1d391kg {
            background: var(--bg-secondary) !important;
            border-right: 1px solid var(--border-color) !important;
        }
        
        /* Input fields light theme */
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox > div > div > div {
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }
        
        /* Metrics light theme */
        .metric-container {
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
        }
        </style>
        """
        
        st.markdown(light_css, unsafe_allow_html=True)

# Global theme toggle instance
theme_toggle = ThemeToggle()

# Convenience functions
def get_current_theme() -> str:
    """Get current theme"""
    return theme_toggle.get_current_theme()

def apply_theme() -> str:
    """Apply current theme and return theme name"""
    theme_toggle.apply_theme_css()
    return theme_toggle.get_current_theme()

def render_theme_toggle():
    """Render theme toggle button"""
    return theme_toggle.render_toggle_button()
