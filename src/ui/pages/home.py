import streamlit as st

from src.site_i18n import site_t
from src.ui.common import language, render_footer, render_header

lang = language()
render_header(site_t("welcome", lang), site_t("site_intro", lang))
st.info(site_t("synthetic", lang))

first, second = st.columns(2)
with first:
    st.markdown("### 🩺")
    st.subheader(site_t("health", lang))
    st.write(site_t("guidance", lang))
    st.page_link("src/ui/pages/public_health.py", label=site_t("explore_health", lang), icon="🩺")
with second:
    st.markdown("### 🏥")
    st.subheader(site_t("hospitals", lang))
    st.write(site_t("trend", lang))
    st.page_link("src/ui/pages/hospitals.py", label=site_t("explore_hospitals", lang), icon="🏥")

st.markdown("---")
st.subheader(site_t("synthetic", lang))
st.write(site_t("disclaimer", lang))
st.page_link("src/ui/pages/login.py", label=site_t("login", lang), icon="🔐")
render_footer()
