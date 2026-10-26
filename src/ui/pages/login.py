
import streamlit as st

from src.authentication import authenticate
from src.staff_accounts import authenticate_staff_account
from src.site_i18n import site_t
from src.ui.common import configured_users, language, render_footer, render_header

lang = language()
render_header(site_t("login", lang), site_t("auth_notice", lang))

users = configured_users()

with st.form("sign_in_form"):
    st.subheader(site_t("credentials", lang))
    username = st.text_input(site_t("username", lang))
    password = st.text_input(site_t("password", lang), type="password")
    submitted = st.form_submit_button(
        site_t("submit", lang),
        use_container_width=True,
    )

if submitted:
    clean_username = username.strip()

    # Keep existing configured-account authentication working.
    authenticated = authenticate(clean_username, password, users)

    # If no configured account matches, check database-backed staff.
    if authenticated is None:
        try:
            authenticated = authenticate_staff_account(
                clean_username,
                password,
            )
        except Exception:
            st.error(
                "The staff account service is temporarily unavailable. "
                "Please try again later."
            )
            st.stop()

    if authenticated is None:
        st.error(
    "Sign-in failed. Invalid credentials, or the staff account is "
    "pending approval or suspended."
)
    else:
        st.session_state["authenticated_username"] = authenticated.username
        st.success(f"{site_t('role', lang)}: {authenticated.role}")
        st.rerun()

if not users:
    st.info(
        "Configured administrator accounts were not found. "
        "Database-backed staff can sign in only after an administrator "
        "has created and activated their accounts."
    )

render_footer()
