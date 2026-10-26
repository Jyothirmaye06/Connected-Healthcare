import logging
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_access import get_all_crowd_data, get_hospitals_df, get_hospital_crowd_history
from src.hospital_intelligence import get_hospital_intelligence
from src.site_i18n import site_t
from src.ui.common import language, render_footer, render_header

LOGGER = logging.getLogger(__name__)
lang = language()
render_header(site_t("hospitals", lang), site_t("site_intro", lang))
st.info(site_t("hospital_data_notice", lang))

try:
    hospitals = get_hospitals_df()
except sqlite3.Error:
    LOGGER.exception("Unable to read registered hospitals.")
    st.error(site_t("unavailable", lang))
    render_footer()
    st.stop()

if hospitals.empty:
    st.info(site_t("no_observations", lang))
    render_footer()
    st.stop()

districts = ["All districts"] + sorted(hospitals["location"].dropna().unique().tolist())
district = st.selectbox(site_t("district", lang), districts, key="public_hospital_district")
visible_hospitals = hospitals if district == "All districts" else hospitals[hospitals["location"] == district]
selected_hospital = st.selectbox(
    site_t("hospital", lang),
    visible_hospitals["name"].tolist(),
    key="public_selected_hospital",
)

try:
    intelligence = get_hospital_intelligence(selected_hospital)
except (OSError, ValueError, KeyError, IndexError, TypeError):
    LOGGER.exception("Unable to calculate hospital intelligence for %s.", selected_hospital)
    st.error(
        "The selected observation or saved prediction artifacts are unavailable. "
        "No forecast is shown until the issue is resolved."
    )
    render_footer()
    st.stop()

try:
    observed_at = pd.Timestamp(intelligence["recorded_at"])
except (TypeError, ValueError):
    observed_at = pd.NaT

if pd.isna(observed_at):
    st.warning(site_t("unavailable", lang))
else:
    age = datetime.now() - observed_at.to_pydatetime().replace(tzinfo=None)
    if age > timedelta(hours=24):
        st.error(f"{site_t('stale', lang)} — {site_t('latest', lang)}: {observed_at}")
    else:
        st.success(f"{site_t('fresh', lang)} — {site_t('latest', lang)}: {observed_at}")
    st.caption(site_t("hospital_data_notice", lang))

st.subheader(f"{intelligence['hospital']} · {intelligence['location']}")
st.caption(f"{site_t('observed', lang)}: {intelligence['recorded_at']}")

metric_columns = st.columns(5)
metrics = [
    ("crowd", intelligence["current_crowd"]),
    ("wait_time", f"{intelligence['current_waiting_minutes']} min"),
    ("arrivals", intelligence["new_patients"]),
    ("discharges", intelligence["discharged_patients"]),
    ("emergencies", intelligence["emergency_cases"]),
]
for column, (label, value) in zip(metric_columns, metrics):
    column.metric(site_t(label, lang), value)

forecast_col1, forecast_col2 = st.columns(2)
forecast_col1.metric(
    site_t("forecast_crowd", lang),
    intelligence["predicted_crowd"],
    delta=intelligence["crowd_delta"],
    help=f"{site_t('forecast', lang)} · {intelligence['prediction_horizon']}",
)
forecast_col2.metric(
    site_t("forecast_wait", lang),
    f"{intelligence['predicted_waiting_minutes']} min",
    delta=f"{intelligence['waiting_delta']} min",
    help=f"{site_t('forecast', lang)} · {intelligence['prediction_horizon']}",
)

st.markdown(f"### {intelligence['status']}")
with st.expander(site_t("alert_reason", lang), expanded=bool(intelligence["reasons"])):
    for reason in intelligence["reasons"]:
        st.write(f"- {reason}")
    st.caption(site_t("disclaimer", lang))

try:
    history = get_hospital_crowd_history(selected_hospital)
except sqlite3.Error:
    LOGGER.exception("Unable to read crowd history for %s.", selected_hospital)
    history = pd.DataFrame()
if history.empty:
    st.info(site_t("no_observations", lang))
else:
    history = history.sort_values("recorded_at")
    history = history.tail(120)
    observed_trace = history[["recorded_at", "people_waiting"]].rename(
        columns={"recorded_at": "time", "people_waiting": site_t("observed", lang)}
    )
    forecast_time = pd.Timestamp(intelligence["recorded_at"]) + pd.Timedelta(hours=1)
    forecast_trace = pd.DataFrame(
        [{"time": forecast_time, site_t("observed", lang): None, site_t("forecast", lang): intelligence["predicted_crowd"]}]
    )
    observed_trace[site_t("forecast", lang)] = None
    trend = pd.concat([observed_trace, forecast_trace], ignore_index=True)
    fig = px.line(
        trend,
        x="time",
        y=[site_t("observed", lang), site_t("forecast", lang)],
        markers=True,
        title=site_t("trend", lang),
    )
    fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)

try:
    all_crowd = get_all_crowd_data()
    comparisons = []
    for _, hospital in visible_hospitals.iterrows():
        try:
            item = get_hospital_intelligence(str(hospital["name"]))
            comparisons.append({
                site_t("hospital", lang): item["hospital"],
                site_t("district", lang): item["location"],
                site_t("crowd", lang): item["current_crowd"],
                site_t("wait_time", lang): item["current_waiting_minutes"],
                site_t("forecast_crowd", lang): item["predicted_crowd"],
                site_t("latest", lang): item["recorded_at"],
                site_t("status", lang): item["status"],
            })
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            LOGGER.exception("Unable to calculate comparison for %s.", hospital["name"])
    if comparisons:
        st.subheader(site_t("comparison", lang))
        st.dataframe(pd.DataFrame(comparisons), use_container_width=True, hide_index=True)
    elif all_crowd.empty:
        st.info(site_t("no_observations", lang))
except sqlite3.Error:
    LOGGER.exception("Unable to load hospital comparison data.")
    st.warning(site_t("unavailable", lang))

st.caption(site_t("hospital_data_notice", lang))
render_footer()
