"""Configuration settings for the Streamlit Salary Explorer."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "SGJobData.db"

# Color Scheme (Job Seeker Focused)
COLORS = {
    "primary": "#2563EB",      # Blue - trust
    "secondary": "#10B981",    # Green - success
    "accent": "#F59E0B",       # Amber - highlights
    "background": "#F9FAFB",   # Light gray
    "text": "#111827",         # Dark gray
    "muted": "#6B7280",        # Gray
    "error": "#EF4444",        # Red
}

# Chart color palette
CHART_COLORS = [
    "#2563EB",  # Primary blue
    "#10B981",  # Green
    "#F59E0B",  # Amber
    "#8B5CF6",  # Purple
    "#EC4899",  # Pink
    "#06B6D4",  # Cyan
    "#84CC16",  # Lime
    "#F97316",  # Orange
]

# Experience bands (predefined)
EXPERIENCE_BANDS = [
    "Entry (0-2 years)",
    "Mid (3-5 years)",
    "Senior (6-10 years)",
    "Executive (10+ years)",
]

# Salary bands
SALARY_BANDS = [
    "< 3K",
    "3K - 5K",
    "5K - 8K",
    "8K - 12K",
    "12K - 20K",
    "20K+",
]

# Page configuration
PAGE_CONFIG = {
    "page_title": "SG Job Market Salary Explorer",
    "page_icon": "💼",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Segment Profiles
SEGMENT_PROFILES = {
    "Everyone": {
        "icon": "👥",
        "description": "All job postings",
        "filter": "",
    },
    "Fresh Graduate": {
        "icon": "🎓",
        "description": "Entry-level roles for new graduates",
        "filter": "AND position_level IN ('Fresh/entry level', 'Junior Executive', 'Non-executive') AND experience_band = 'Entry (0-2 years)'",
    },
    "Mid-Career Switcher": {
        "icon": "🔄",
        "description": "Roles for professionals exploring new industries",
        "filter": "AND position_level IN ('Executive', 'Professional') AND experience_band IN ('Mid (3-5 years)', 'Senior (6-10 years)')",
    },
    "Experienced Professional": {
        "icon": "⭐",
        "description": "Senior and leadership positions",
        "filter": "AND position_level IN ('Manager', 'Senior Executive', 'Middle Management', 'Senior Management') AND experience_band IN ('Senior (6-10 years)', 'Executive (10+ years)')",
    },
}

# Chart defaults
CHART_HEIGHT = 400
CHART_MARGIN = dict(l=20, r=20, t=40, b=20)
