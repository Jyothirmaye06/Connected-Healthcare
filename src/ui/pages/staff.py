import logging
import sqlite3
from datetime import datetime, time

import streamlit as st

from src.authentication import user_can_access_hospital
from src.data_access import get_hospitals_df
from src.data_validation import ValidationError
from src.site_i18n import site_t
from src.staff_portal import (
    AuthorizationError,
    ObservationTimestampError,
    get_observation_audit,
    submit_staff_observation,
)
from src.ui.common import current_user, language, render_footer, render_header

LOGGER = logging.getLogger(__name__)
lang = language()
render_header(site_t("staff", lang), site_t("auth_notice", lang))
user = current_user()
if user is None or user.role not in {"staff", "admin"}:
    st.error(site_t("access_denied", lang))
    render_footer()
    st.stop()

try:
    hospitals = get_hospitals_df()
except sqlite3.Error:
    LOGGER.exception("Unable to load hospitals for staff data entry.")
    st.error(site_t("unavailable", lang))
    render_footer()
    st.stop()

authorized = hospitals[
    hospitals["id"].apply(lambda hospital_id: user_can_access_hospital(user, int(hospital_id)))
]
if authorized.empty:
    st.error(site_t("not_assigned", lang))
    render_footer()
    st.stop()

st.info(site_t("staff_data_notice", lang))
with st.form("staff_observation_form", clear_on_submit=True):
    hospital_id = st.selectbox(
        site_t("hospital", lang),
        authorized["id"].astype(int).tolist(),
        format_func=lambda value: (
            f"{authorized.loc[authorized['id'] == value, 'name'].iloc[0]} "
            f"({authorized.loc[authorized['id'] == value, 'location'].iloc[0]})"
        ),
    )
    date_col, time_col = st.columns(2)
    with date_col:
        observation_date = st.date_input(site_t("recorded_at", lang), value=datetime.now().date())
    with time_col:
        observation_time = st.time_input(site_t("time", lang), value=datetime.now().time().replace(second=0, microsecond=0))
    metric_cols = st.columns(3)
    with metric_cols[0]:
        people_waiting = st.number_input(site_t("people", lang), min_value=0, max_value=500, value=0, step=1)
        arrivals = st.number_input(site_t("new_patients", lang), min_value=0, max_value=200, value=0, step=1)
    with metric_cols[1]:
        waiting_minutes = st.number_input(site_t("minutes", lang), min_value=0, max_value=720, value=0, step=1)
        discharged = st.number_input(site_t("discharges", lang), min_value=0, max_value=200, value=0, step=1)
    with metric_cols[2]:
        emergencies = st.number_input(site_t("emergency", lang), min_value=0, max_value=50, value=0, step=1)
        holiday =         st.selectbox(
            site_t("holiday", lang),
            [0, 1],
            format_func=lambda value: site_t("yes", lang) if value else site_t("no", lang),
        )
    special_event = st.text_input(site_t("special_event", lang), max_chars=50)
    submitted = st.form_submit_button(site_t("submit_observation", lang), use_container_width=True)

if submitted:
    payload = {
        "hospital_id": hospital_id,
        "people_waiting": people_waiting,
        "waiting_minutes": waiting_minutes,
        "new_patients": arrivals,
        "discharged_patients": discharged,
        "emergency_cases": emergencies,
        "holiday": holiday,
        "special_event": special_event,
        "recorded_at": datetime.combine(observation_date, observation_time),
    }
    try:
        result = submit_staff_observation(user, payload)
        st.success(
            f"{site_t('success', lang)} Observation #{result['observation_id']} · "
            f"{result['recorded_at']}"
        )
    except AuthorizationError as error:
        st.error(str(error))
    except (ValidationError, ObservationTimestampError) as error:
        st.error(str(error))
    except sqlite3.Error:
        LOGGER.exception("Database error while saving staff observation.")
        st.error(site_t("submission_failed", lang))

st.subheader(site_t("recent_audit", lang))
try:
    audit = get_observation_audit(user, limit=25)
    if audit.empty:
        st.info(site_t("no_observations", lang))
    else:
        st.dataframe(audit, use_container_width=True, hide_index=True)
except (AuthorizationError, sqlite3.Error):
    LOGGER.exception("Unable to load staff audit history.")
    st.error(site_t("unavailable", lang))
render_footer()
