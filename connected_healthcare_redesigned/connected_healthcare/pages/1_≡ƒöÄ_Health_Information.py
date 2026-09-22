"""
pages/1_🔎_Health_Information.py
--------------------------------
Health condition search + general awareness information.

This page reports what is in the database and shares general educational
information. It deliberately does NOT diagnose, does not interpret a user's
personal symptoms, and does not recommend medication.

Kept deliberately simple: one trend chart (with a plain-language
explanation), a short hospital breakdown, an age-group chart, severity as
simple counts, and bullet-point health information. No raw record tables.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

import data_service
from config import TREND_WINDOW_DAYS
from utils import charts, ui
from utils.analysis_utils import (
    age_distribution,
    condition_trend_table,
    daily_case_counts,
    format_trend_label,
    hospital_distribution,
    severity_distribution,
)

ui.setup_page("Health Information", icon="🔎")
ui.hero("Health Information • Reported trends & general awareness")

location = ui.location_selector()
version = data_service.data_version()
ui.demo_badge()

cases_df = data_service.cases(location, version)
known_conditions = data_service.all_known_conditions(version)

if not known_conditions:
    ui.empty_state("No conditions are available in the database yet.")
    ui.sidebar_footer()
    st.stop()

# --------------------------------------------------------------------------
# Condition selection
# --------------------------------------------------------------------------
st.markdown("## 🔎 Search Health Information")

default_index = 0
preselected = st.session_state.get("home_condition_search")
if preselected in known_conditions:
    default_index = known_conditions.index(preselected)

condition = st.selectbox("Select a health condition", known_conditions,
                         index=default_index, key="explorer_condition")

condition_cases = (
    cases_df[cases_df["condition"] == condition]
    if not cases_df.empty else cases_df
)

st.markdown(f"# {condition}")
st.caption(f"Reported records in {location} • synthetic demo data")

# --------------------------------------------------------------------------
# Headline numbers
# --------------------------------------------------------------------------
trend_table = condition_trend_table(cases_df)
trend_row = None
if not trend_table.empty:
    match = trend_table[trend_table["condition"] == condition]
    if not match.empty:
        trend_row = match.iloc[0]

total_cases = 0 if condition_cases is None or condition_cases.empty else len(condition_cases)

k1, k2, k3 = st.columns(3)
with k1:
    ui.metric_card("Reported Cases", f"{total_cases:,}", f"In {location}")
with k2:
    if trend_row is not None:
        ui.metric_card("Recent Trend", format_trend_label(trend_row),
                       f"{trend_row['recent_cases']} recent vs {trend_row['previous_cases']} previous")
    else:
        ui.metric_card("Recent Trend", "Not available", "Insufficient historical data")
with k3:
    hospitals_reporting = (
        0 if condition_cases is None or condition_cases.empty
        else condition_cases["hospital_name"].nunique()
    )
    ui.metric_card("Hospitals Reporting", hospitals_reporting, f"In {location}")

if condition_cases is None or condition_cases.empty:
    st.warning(
        f"No reported cases of {condition} are recorded for {location}. "
        "General awareness information is still shown below."
    )

st.markdown("---")

# --------------------------------------------------------------------------
# Recent trend — one chart, always visible, always explained
# --------------------------------------------------------------------------
st.markdown("### 📈 Recent Trend")
ui.chart_note(f"This chart shows how many {condition} cases were reported over time.")

fig = charts.case_trend_line(
    daily_case_counts(condition_cases, days=60),
    title=f"{condition} — reported cases over the last 60 days",
)
if fig:
    st.plotly_chart(fig, use_container_width=True)
    if trend_row is not None and trend_row["enough_data"]:
        st.caption(
            f"{format_trend_label(trend_row)} — comparing the last "
            f"{TREND_WINDOW_DAYS} days with the previous {TREND_WINDOW_DAYS} days."
        )
    else:
        st.caption("Not enough historical data to identify a reliable trend.")
else:
    ui.empty_state(f"No reported {condition} cases to chart for {location}.")

st.markdown("---")

# --------------------------------------------------------------------------
# Hospital distribution — a short list, not a chart or raw table
# --------------------------------------------------------------------------
st.markdown("### 🏥 Which Hospitals Reported This")

dist = hospital_distribution(condition_cases)
if dist.empty:
    ui.empty_state("No hospital-wise data available for this condition.")
else:
    top_two = dist.head(2)
    other_total = int(dist["cases"].iloc[2:].sum()) if len(dist) > 2 else 0

    for _, row in top_two.iterrows():
        ui.condition_row(row["hospital_name"], f"{row['cases']:,} cases")
    if other_total > 0:
        ui.condition_row("Other hospitals", f"{other_total:,} cases")

st.markdown("---")

# --------------------------------------------------------------------------
# Age groups & severity — kept to two simple visuals
# --------------------------------------------------------------------------
st.markdown("### 👥 Age Groups & Severity")

col_a, col_b = st.columns(2)
with col_a:
    ui.chart_note(f"How reported {condition} cases are spread across age groups.")
    fig = charts.age_bar(age_distribution(condition_cases), title=f"{condition} — age groups")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        ui.empty_state("No age-group data available.")

with col_b:
    st.markdown("**Severity of reported cases**")
    sev = severity_distribution(condition_cases)
    if sev["cases"].sum() == 0:
        ui.empty_state("No severity data available.")
    else:
        for _, row in sev.iterrows():
            ui.condition_row(row["severity"], f"{row['cases']:,} cases")

st.markdown("---")

# --------------------------------------------------------------------------
# General educational information
# --------------------------------------------------------------------------
st.markdown("## 📚 General Health Information")

info = data_service.health_information(condition, version)
if not info:
    ui.empty_state(
        f"General health information for {condition} has not been added yet.",
        "An administrator can add it from the 🔐 Admin page.",
    )
else:
    with st.expander("🤒 Common symptoms", expanded=True):
        ui.bullet_list(info["symptoms"])
    with st.expander("🛡️ General prevention", expanded=True):
        ui.bullet_list(info["prevention"])
    with st.expander("🏥 When to seek medical help", expanded=True):
        ui.bullet_list(info["when_to_seek_help"])
    st.caption("Please consult a qualified healthcare professional for personal medical concerns.")

st.markdown("---")
ui.medical_disclaimer()
ui.sidebar_footer()
