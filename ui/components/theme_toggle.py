"""
Theme toggle component
Provides dark/light theme switching functionality
"""

import streamlit as st
from typing import Optional


class ThemeToggle:
    """Theme toggle component for dark/light mode switching"""

    def __init__(self):
        self.theme_key = "app_theme"
        self.default_theme = "light"

        # Initialize theme if not set
        if self.theme_key not in st.session_state:
            st.session_state[self.theme_key] = self.default_theme

    def get_current_theme(self) -> str:
        """Get current theme from session state"""
        return st.session_state.get(self.theme_key, self.default_theme)

    def set_theme(self, theme: str):
        """Set current theme in session state"""
        st.session_state[self.theme_key] = theme

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        current = self.get_current_theme()
        new_theme = "dark" if current == "light" else "light"
        self.set_theme(new_theme)
        st.rerun()

    def render_toggle_button(self, container=None) -> Optional[str]:
        """Render theme toggle button with modern styling"""
        current_theme = self.get_current_theme()

        if container is None:
            container = st

        # Icons and text for button
        if current_theme == "light":
            icon, text, new_theme = "🌙", "Dark Mode", "dark"
        else:
            icon, text, new_theme = "☀️", "Light Mode", "light"

        # Styled toggle button (using markdown + JS hack for style)
        button_html = f"""
        <style>
        .theme-toggle-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 6px 14px;
            font-size: 14px;
            font-weight: 500;
            border-radius: 20px;
            border: 1px solid var(--border-color, #ccc);
            cursor: pointer;
            background: var(--bg-secondary, #f1f5f9);
            transition: all 0.3s ease;
        }}
        .theme-toggle-btn:hover {{
            background: var(--bg-tertiary, #e2e8f0);
            transform: scale(1.05);
        }}
        </style>
        <button class="theme-toggle-btn" onclick="window.parent.postMessage({{'themeToggle': true}}, '*')">
            {icon} {text}
        </button>
        """

        container.markdown(button_html, unsafe_allow_html=True)

        # JS to persist theme choice & trigger rerun
        st.markdown(
            """
            <script>
            const currentTheme = localStorage.getItem("streamlit_theme") || "light";

            // Store theme toggle action
            window.addEventListener("message", (event) => {
                if (event.data.themeToggle) {
                    const newTheme = currentTheme === "light" ? "dark" : "light";
                    localStorage.setItem("streamlit_theme", newTheme);
                    window.location.reload();
                }
            });
            </script>
            """,
            unsafe_allow_html=True,
        )

        return current_theme

    def render_sidebar_toggle(self):
        """Render theme toggle in sidebar"""
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🎨 Theme")
            self.render_toggle_button()

    def render_header_toggle(self):
        """Render theme toggle in header area"""
        col1, col2, col3 = st.columns([6, 1, 1])
        with col3:
            self.render_toggle_button()

    def apply_theme_css(self):
        """Apply theme-specific CSS"""
        current_theme = self.get_current_theme()
        if current_theme == "dark":
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

    def _apply_dark_theme(self):
        """Dark theme CSS"""
        dark_css = """
        <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-color: #475569;
        }

        .stApp {
            background: linear-gradient(135deg, #0f172a, #1e293b 50%, #334155) !important;
            color: var(--text-primary) !important;
        }

        .main .block-container {
            background: rgba(15, 23, 42, 0.95) !important;
            border: 1px solid var(--border-color) !important;
        }

        section[data-testid="stSidebar"] {
            background: var(--bg-secondary) !important;
            border-right: 1px solid var(--border-color) !important;
        }

        input, textarea, select {
            background: var(--bg-tertiary) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }
        </style>
        """
        st.markdown(dark_css, unsafe_allow_html=True)

    def _apply_light_theme(self):
        """Light theme CSS"""
        light_css = """
        <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
        }

        .stApp {
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            color: var(--text-primary) !important;
        }

        .main .block-container {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 1px solid var(--border-color) !important;
        }

        section[data-testid="stSidebar"] {
            background: var(--bg-secondary) !important;
            border-right: 1px solid var(--border-color) !important;
        }

        input, textarea, select {
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }
        </style>
        """
        st.markdown(light_css, unsafe_allow_html=True)


# Global instance
theme_toggle = ThemeToggle()


# Convenience functions
def init_theme():
    """Initialize and apply theme at app start"""
    theme = theme_toggle.get_current_theme()
    theme_toggle.apply_theme_css()
    return theme


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
