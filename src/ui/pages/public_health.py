import logging
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_access import get_health_cases_df, get_health_information_df
from src.site_i18n import site_t, translate_guidance
from src.ui.common import language, render_footer, render_header

LOGGER = logging.getLogger(__name__)
lang = language()
render_header(site_t("health", lang), site_t("site_intro", lang))
st.info(site_t("synthetic", lang))

try:
    cases = get_health_cases_df()
    guidance = get_health_information_df()
except sqlite3.Error:
    LOGGER.exception("Unable to load public health demonstration data.")
    st.error(site_t("unavailable", lang))
    render_footer()
    st.stop()

if cases.empty:
    st.info(site_t("no_observations", lang))
else:
    cases["date"] = pd.to_datetime(cases["date"], errors="coerce")
    cases = cases.dropna(subset=["date"])
    if cases.empty:
        st.info(site_t("no_observations", lang))
    else:
        all_conditions = site_t("all_conditions", lang)
        all_districts = site_t("all_districts", lang)
        conditions = [all_conditions] + sorted(cases["condition"].dropna().unique().tolist())
        districts = [all_districts] + sorted(cases["location"].dropna().unique().tolist())
        f1, f2, f3 = st.columns(3)
        with f1:
            selected_condition = st.selectbox(site_t("condition", lang), conditions)
        with f2:
            selected_district = st.selectbox(site_t("district", lang), districts)
        with f3:
            st.caption(f"{site_t('latest_case_date', lang)}: **{cases['date'].max().date().isoformat()}**")

        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input(
                site_t("start_date", lang),
                value=cases["date"].min().date(),
                min_value=cases["date"].min().date(),
                max_value=cases["date"].max().date(),
                key="health_start_date",
            )
        with date_col2:
            end_date = st.date_input(
                site_t("end_date", lang),
                value=cases["date"].max().date(),
                min_value=cases["date"].min().date(),
                max_value=cases["date"].max().date(),
                key="health_end_date",
            )

        filtered = cases.copy()
        if selected_condition != all_conditions:
            filtered = filtered[filtered["condition"] == selected_condition]
        if selected_district != all_districts:
            filtered = filtered[filtered["location"] == selected_district]
        filtered = filtered[
            filtered["date"].dt.date.between(start_date, end_date)
        ]

        st.caption(site_t("data_source", lang))
        if start_date > end_date:
            st.warning("Choose a start date on or before the end date.")
        elif filtered.empty:
            st.info(site_t("no_observations", lang))
        else:
            total = int(filtered["cases"].sum())
            st.metric(site_t("reported_cases", lang), f"{total:,}")
            st.caption(site_t("trend_explanation", lang))
            by_day = (
                filtered.groupby(["date", "condition"], as_index=False)["cases"]
                .sum()
                .sort_values("date")
            )
            fig = px.line(
                by_day,
                x="date",
                y="cases",
                color="condition",
                markers=True,
                labels={"date": site_t("recorded_at", lang), "cases": site_t("reported_cases", lang)},
                title=site_t("case_trend", lang),
            )
            fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=55, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.caption(site_t("no_hospital_cases", lang))
        st.caption(site_t("no_age", lang))

st.subheader(site_t("guidance", lang))
st.caption(site_t("english_copy", lang))
if not guidance.empty:
    for _, item in guidance.iterrows():
        with st.expander(str(item["condition"])):
            st.markdown(
                f"**{site_t('symptoms', lang)}:** "
                f"{translate_guidance(str(item['condition']), 'symptoms', str(item['symptoms'] or ''), lang) or site_t('not_provided', lang)}"
            )
            st.markdown(
                f"**{site_t('prevention', lang)}:** "
                f"{translate_guidance(str(item['condition']), 'prevention', str(item['prevention'] or ''), lang) or site_t('not_provided', lang)}"
            )
            st.markdown(
                f"**{site_t('seek_help', lang)}:** "
                f"{translate_guidance(str(item['condition']), 'when_to_seek_help', str(item['when_to_seek_help'] or ''), lang) or site_t('not_provided', lang)}"
            )

st.subheader(site_t("official_links", lang))
st.markdown(
    f"- [{site_t('source_health', lang)}](https://www.cdc.gov/respiratory-viruses/prevention/index.html)\n"
    f"- [{site_t('source_who_dengue', lang)}](https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue)\n"
    f"- [{site_t('source_who_diabetes', lang)}](https://www.who.int/news-room/fact-sheets/detail/diabetes)"
)
st.caption(
    site_t("source_unverified", lang)
)
st.warning(site_t("disclaimer", lang))
render_footer()
