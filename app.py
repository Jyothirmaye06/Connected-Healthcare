
"""Connected Healthcare multipage Streamlit application."""

import streamlit as st

from src.site_i18n import site_t
from src.ui.common import configured_users, language, render_global_sidebar


st.set_page_config(
    page_title="Connected Healthcare",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --navy: #102a43;
        --teal: #087e8b;
        --aqua: #d9f3f2;
        --muted: #52677a;
    }

    .stApp {
        background: #f7fafc;
    }

    [data-testid="stSidebar"] {
        background: #102a43;
    }

    [data-testid="stSidebar"] * {
        color: #f7fafc;
    }

    [data-testid="stSidebar"] button {
        border-color: #71d4d1;
    }

    .eyebrow {
        color: #087e8b;
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: -.7rem;
    }

    h1, h2, h3 {
        color: #102a43;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d9e5ec;
        border-top: 3px solid #087e8b;
        border-radius: .65rem;
        padding: .85rem 1rem;
    }

    [data-testid="stMetricLabel"] {
        color: #52677a;
    }

    a {
        color: #087e8b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "language" not in st.session_state:
    st.session_state["language"] = "en"

users = configured_users()
user = render_global_sidebar(users)
lang = language()

# Public navigation pages
pages = [
    st.Page(
        "src/ui/pages/home.py",
        title=site_t("home", lang),
        icon="🏠",
        default=True,
    ),
    st.Page(
        "src/ui/pages/public_health.py",
        title=site_t("health", lang),
        icon="🏥",
    ),
    st.Page(
        "src/ui/pages/hospitals.py",
        title=site_t("hospitals", lang),
        icon="🏥",
    ),
    st.Page(
        "src/ui/pages/dataset.py",
        title="Dataset & Updates",
        icon="📊",
    ),
    st.Page(
        "src/ui/pages/login.py",
        title=site_t("login", lang),
        icon="🔐",
    ),
]

# Show the Staff Portal to authenticated staff and administrators
if user is not None and user.role in {"staff", "admin"}:
    pages.append(
        st.Page(
            "src/ui/pages/staff.py",
            title=site_t("staff", lang),
            icon="📋",
        )
    )

navigation = st.navigation(pages, position="sidebar")
navigation.run()
