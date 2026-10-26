"""Shared navigation, styling, authentication, and page framing."""

import logging
import sqlite3
from collections.abc import Mapping
from typing import Any, Dict, Optional

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from src.authentication import AuthenticatedUser, resolve_authenticated_user, user_has_role
from src.data_access import get_hospitals_df
from src.site_i18n import site_t

LOGGER = logging.getLogger(__name__)


def configured_users() -> Dict[str, Any]:
    """Reads accounts from Streamlit secrets; missing configuration means no accounts."""
    try:
        configured = st.secrets.get("users", {})
    except StreamlitSecretNotFoundError:
        return {}
    if not isinstance(configured, Mapping):
        LOGGER.error("The Streamlit secrets 'users' value must be a table.")
        return {}
    return dict(configured)



def current_user(users: Optional[Mapping[str, Any]] = None) -> Optional[AuthenticatedUser]:
    """Resolve configured users first, then verify database-backed staff accounts."""
    username = st.session_state.get("authenticated_username")
    if not username:
        return None

    configured = users if users is not None else configured_users()

    # Preserve existing administrator and configured-account authentication.
    user = resolve_authenticated_user(username, configured)
    if user is not None:
        return user

    # Database-backed staff must still exist and remain active.
    from src.staff_accounts import get_active_staff_user

    return get_active_staff_user(username)



def language() -> str:
    return st.session_state.get("language", "en")


def tr(key: str) -> str:
    return site_t(key, language())


def render_global_sidebar(users: Mapping[str, Any]) -> Optional[AuthenticatedUser]:
    """Renders language and authentication state, then returns the server-resolved user."""
    lang = language()
    st.sidebar.markdown(f"## {site_t('app_title', lang)}")
    language_options = {"English": "en", "తెలుగు (Telugu)": "te", "हिन्दी (Hindi)": "hi"}
    current_code = language()
    current_label = next(
        (label for label, code in language_options.items() if code == current_code),
        "English",
    )
    selected = st.sidebar.selectbox(
        site_t("language_selector", current_code),
        list(language_options),
        index=list(language_options).index(current_label),
        key="site_language_selector",
    )
    st.session_state["language"] = language_options[selected]
    st.sidebar.divider()
    user = current_user(users)
    if user is None:
        st.sidebar.caption(site_t("auth_notice", language()))
    else:
        st.sidebar.markdown(f"**{user.username}**")
        st.sidebar.caption(f"{site_t('role', language())}: {user.role}")
        if st.sidebar.button(site_t("logout", language()), use_container_width=True):
            st.session_state.pop("authenticated_username", None)
            st.rerun()
    return user


def require_role(required_role: str, users: Optional[Mapping[str, Any]] = None) -> AuthenticatedUser:
    """Stops the page unless the current configured identity satisfies its role."""
    user = current_user(users)
    if not user_has_role(user, required_role):
        st.error(site_t("access_denied", language()))
        st.stop()
    return user


def render_header(title: str, description: str, eyebrow: str = "Connected Healthcare") -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.write(description)


def render_footer() -> None:
    st.divider()
    st.caption(site_t("footer", language()))
    st.caption(site_t("disclaimer", language()))


def render_no_hospitals() -> bool:
    """Shows a non-destructive empty state if the existing DB lacks hospital rows."""
    try:
        hospitals = get_hospitals_df()
    except sqlite3.Error:
        LOGGER.exception("Unable to read the hospital list.")
        st.error(site_t("unavailable", language()))
        return True
    if hospitals.empty:
        st.warning("No registered hospital data is available in the configured database.")
        return True
    return False
