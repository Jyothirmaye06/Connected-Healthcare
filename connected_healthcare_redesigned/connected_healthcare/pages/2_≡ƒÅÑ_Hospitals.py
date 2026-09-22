"""
pages/2_🏥_Hospitals.py
-----------------------
Hospital-wise crowd and waiting information.

Terminology used deliberately throughout this page:
  * "Current reported crowd" — the latest value submitted by hospital staff
    through the Admin page. It is NOT a live feed from a hospital system.
  * "Predicted" values are always labelled as estimates, produced by the
    crowd-prediction model, and link through to the full Crowd Prediction
    page for more control.
"""

from datetime import datetime, timedelta

import streamlit as st

import data_service
from config import CROWD_THRESHOLDS
from utils import charts, ui
from utils.analysis_utils import (
    annotate_crowd_status,
    crowd_status,
    describe_time_ago,
    format_hour,
    hourly_average_crowd,
    queue_profile,
)

ui.setup_page("Hospitals", icon="🏥")
ui.hero("Hospitals • Current reported waiting information")

location = ui.location_selector()
version = data_service.data_version()
ui.demo_badge()

latest_df = annotate_crowd_status(data_service.latest_queue(location, version))

if latest_df is None or latest_df.empty:
    ui.empty_state(
        f"No hospitals are registered for {location} yet.",
        "An administrator can add hospitals from the 🔐 Admin page.",
    )
    ui.sidebar_footer()
    st.stop()

# --------------------------------------------------------------------------
# Location summary
# --------------------------------------------------------------------------
reporting = latest_df["patients_waiting"].notna().sum()
total_waiting = int(latest_df["patients_waiting"].fillna(0).sum())
busiest = (
    latest_df.dropna(subset=["patients_waiting"])
    .sort_values("patients_waiting", ascending=False)
)

c1, c2, c3 = st.columns(3)
with c1:
    ui.metric_card("Hospitals", len(latest_df), f"In {location}")
with c2:
    ui.metric_card("Total Patients Waiting", f"{total_waiting:,}",
                   f"Across {int(reporting)} reporting hospitals")
with c3:
    if busiest.empty:
        ui.metric_card("Busiest Right Now", "No data", "No crowd reports yet")
    else:
        top = busiest.iloc[0]
        ui.metric_card("Busiest Right Now", top["hospital_name"],
                       f"{int(top['patients_waiting'])} patients waiting")

st.caption(
    f"🟢 Less busy: up to {CROWD_THRESHOLDS['low_max']} waiting • "
    f"🟡 Moderately busy: {CROWD_THRESHOLDS['low_max'] + 1}–{CROWD_THRESHOLDS['moderate_max']} • "
    f"🔴 Very busy: above {CROWD_THRESHOLDS['moderate_max']}."
)

st.markdown("---")

# --------------------------------------------------------------------------
# Hospital cards — one card per hospital, visually separated
# --------------------------------------------------------------------------
st.markdown(f"## 🏥 Hospitals in {location}")

card_cols = st.columns(2)
for index, (_, row) in enumerate(latest_df.iterrows()):
    with card_cols[index % 2]:
        ui.hospital_crowd_card(row)

ui.chart_note(f"Comparing the current reported crowd across hospitals in {location}.")
fig = charts.crowd_comparison_bar(latest_df,
                                  title=f"Current reported crowd — {location}")
if fig:
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --------------------------------------------------------------------------
# Hospital details
# --------------------------------------------------------------------------
st.markdown("## 🔍 Hospital Details")

hospital_names = latest_df["hospital_name"].tolist()
selected_name = st.selectbox("Select a hospital to view details", hospital_names,
                             key="crowd_hospital_select")
selected = latest_df[latest_df["hospital_name"] == selected_name].iloc[0]
hospital_id = int(selected["hospital_id"])

history_days = st.slider("History window (days)", min_value=3, max_value=28,
                         value=14, step=1)
history = data_service.queue_history(version, hospital_id=hospital_id,
                                     days=history_days)

st.markdown(f"### {selected_name}")
st.caption(selected["location"])

d1, d2, d3 = st.columns(3)
has_current = selected["patients_waiting"] == selected["patients_waiting"] \
    and selected["patients_waiting"] is not None

with d1:
    ui.metric_card(
        "Current Reported Crowd",
        f"{int(selected['patients_waiting'])} waiting" if has_current else "Not reported",
        describe_time_ago(selected["recorded_at"]) if has_current else "—",
    )
with d2:
    ui.metric_card(
        "Estimated Waiting Time",
        f"{int(selected['estimated_waiting_minutes'])} min" if has_current else "Not reported",
        "As reported by hospital staff",
    )
with d3:
    status = selected.get("status", "Unknown")
    ui.metric_card("Status", status, "Based on reported patients waiting")

if history is None or history.empty:
    ui.empty_state(
        f"No crowd history has been recorded for {selected_name} in the last "
        f"{history_days} days.",
        "Records are created each time hospital staff submit an update on the Admin page.",
    )
else:
    profile = queue_profile(history)

    st.markdown("#### Historical Crowd")
    ui.chart_note(f"How {selected_name}'s reported crowd has changed over the last {history_days} days.")
    fig = charts.crowd_history_line(
        history, title=f"{selected_name} — reported crowd (last {history_days} days)"
    )
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    p1, p2 = st.columns(2)
    with p1:
        ui.metric_card("Busiest Time", format_hour(profile["busiest_hour"]),
                       f"Busiest day: {profile['busiest_day'] or 'Not available'}")
    with p2:
        ui.metric_card("Less Busy Time", format_hour(profile["quietest_hour"]),
                       "Based on reported history")
    st.caption("Typical crowd is higher during the busiest period shown above.")

    with st.expander("See the typical pattern by hour of day"):
        ui.chart_note("Average reported crowd for each hour of the day, based on all recorded history.")
        fig = charts.hourly_pattern_bar(
            hourly_average_crowd(history),
            title=f"{selected_name} — average crowd by hour",
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Planning a visit? Hours with a lower average reported crowd are "
                "usually less busy, though actual conditions vary."
            )

st.markdown("---")

# --------------------------------------------------------------------------
# Predicted crowd — short preview, full control on the Crowd Prediction page
# --------------------------------------------------------------------------
st.markdown("### 🔮 Predicted Crowd")
st.caption("Estimated using historical crowd patterns — not live hospital data.")

model, error = data_service.crowd_model(location, version)
if model is None:
    ui.empty_state(
        "Prediction is currently unavailable because there is not enough historical data.",
    )
else:
    upcoming = datetime.now() + timedelta(hours=2)
    try:
        preview = model.predict(hospital_id, upcoming)
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            ui.metric_card(
                f"Expected around {upcoming.strftime('%I:%M %p')}",
                f"{preview['predicted_patients_waiting']} patients waiting",
                f"Status estimate: {crowd_status(preview['predicted_patients_waiting'])}",
            )
        with pcol2:
            ui.metric_card("Predicted Wait", f"~{preview['predicted_waiting_minutes']} minutes",
                           "Prediction based on historical data")
    except Exception:
        ui.empty_state(f"No prediction is available yet for {selected_name}.")

st.page_link("pages/3_🔮_Crowd_Prediction.py",
             label=f"See the full predicted crowd for {selected_name} →", icon="🔮")

st.markdown("---")
st.info(
    "These figures are the latest values reported by hospital staff for this "
    "prototype. They are not a live integration with hospital systems. "
    "For emergencies, seek appropriate emergency medical care."
)
ui.sidebar_footer()
