"""
app.py — Connected Healthcare
-----------------------------
Home page of the platform.

Run with:  streamlit run app.py

This page intentionally shows ONLY the most useful information: a one-line
health overview, a handful of the most-reported conditions, hospital crowd
cards, a one-line trend headline, and health-condition search. Full charts,
tables and technical detail live on the dedicated pages — Health
Information, Hospitals, and Crowd Prediction (see the sidebar).

Everything shown here is computed live from the SQLite database for the
currently selected location. Nothing on this page is hard-coded.
"""

import streamlit as st

import data_service
from utils import ui
from utils.analysis_utils import (
    annotate_crowd_status,
    condition_distribution,
    condition_trend_table,
    format_trend_label,
    overview_metrics,
)

ui.setup_page("Home", icon="🏥")
ui.hero()

# --------------------------------------------------------------------------
# Location selection — drives every query on this page
# --------------------------------------------------------------------------
selector_col, refresh_col = st.columns([3, 1])
with selector_col:
    location = ui.location_selector()
with refresh_col:
    st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh dashboard", use_container_width=True):
        data_service.refresh()
        st.rerun()

version = data_service.data_version()
ui.demo_badge()

hospitals_df = data_service.hospitals(location, version)
cases_df = data_service.cases(location, version)

if hospitals_df.empty:
    ui.empty_state(
        f"No hospitals are registered for {location} yet.",
        "An administrator can add hospitals from the 🔐 Admin page.",
    )
    ui.sidebar_footer()
    st.stop()

# --------------------------------------------------------------------------
# 1. Health overview — one short, plain-language summary
# --------------------------------------------------------------------------
st.markdown(f"## 📊 Health Overview — {location}")

metrics = overview_metrics(cases_df, hospitals_df)

if cases_df.empty:
    ui.summary_card(
        f"No health-condition reports have been recorded for <b>{location}</b> yet."
    )
else:
    ui.summary_card(
        f"The most reported condition in <b>{location}</b> is "
        f"<b>{metrics['top_condition']}</b> ({metrics['top_condition_cases']:,} reported cases). "
        f"The most affected age group is <b>{metrics['top_age_band']}</b>."
    )

st.markdown("")

# --------------------------------------------------------------------------
# 2. Recent health conditions — a short list, not a chart
# --------------------------------------------------------------------------
st.markdown("## 🩺 Recent Health Conditions")

top_conditions = condition_distribution(cases_df, top_n=4)

if top_conditions.empty:
    ui.empty_state(f"No reported conditions are available for {location} yet.")
else:
    for _, row in top_conditions.iterrows():
        ui.condition_row(row["condition"], f"{row['cases']:,} reported cases")

    st.page_link(
        "pages/1_🔎_Health_Information.py",
        label="Explore Health Information →", icon="🔎",
    )

st.markdown("---")

# --------------------------------------------------------------------------
# 3. Hospital crowd — one card per hospital
# --------------------------------------------------------------------------
st.markdown(f"## 🏥 Hospital Crowd in {location}")
st.caption(
    "Latest crowd values reported by hospital staff. These are reported "
    "figures, not a live feed from hospital systems."
)

latest_df = annotate_crowd_status(data_service.latest_queue(location, version))

if latest_df is None or latest_df.empty:
    ui.empty_state(f"No hospital crowd information has been reported for {location} yet.")
else:
    card_cols = st.columns(2)
    for index, (_, row) in enumerate(latest_df.iterrows()):
        with card_cols[index % 2]:
            ui.hospital_crowd_card(row)

    st.page_link("pages/2_🏥_Hospitals.py",
                 label="View full hospital crowd details →", icon="🏥")

st.markdown("---")

# --------------------------------------------------------------------------
# 4. Health trends — a single headline, not a chart
# --------------------------------------------------------------------------
st.markdown("## 📈 Health Trends")

trend_table = condition_trend_table(cases_df)
usable_trends = trend_table[trend_table["enough_data"]] if not trend_table.empty else trend_table

if usable_trends.empty:
    ui.empty_state("Not enough historical data to identify a reliable trend yet.")
else:
    top = usable_trends.iloc[0]
    if top["direction"] == "rising":
        headline = f"📈 <b>{top['condition']}</b> reports increased recently."
    elif top["direction"] == "falling":
        headline = f"📉 <b>{top['condition']}</b> reports decreased recently."
    else:
        headline = f"➖ <b>{top['condition']}</b> reports have stayed about the same."
    ui.summary_card(
        f"{headline}<br>{top['recent_cases']} recent reports vs "
        f"{top['previous_cases']} in the previous period."
    )

st.page_link("pages/1_🔎_Health_Information.py",
             label="View Health Trends →", icon="📈")

st.markdown("---")

# --------------------------------------------------------------------------
# 5. Search health information
# --------------------------------------------------------------------------
st.markdown("## 🔎 Look for Health Information")

known_conditions = data_service.all_known_conditions(version)
if not known_conditions:
    ui.empty_state("No health information has been added to the database yet.")
else:
    chosen = st.selectbox("Search or select a health condition", known_conditions,
                          key="home_condition_search")
    info = data_service.health_information(chosen, version)
    condition_cases = cases_df[cases_df["condition"] == chosen] if not cases_df.empty else cases_df
    reported = 0 if condition_cases is None or condition_cases.empty else len(condition_cases)

    ui.summary_card(
        f"<b>{chosen}</b> — {reported:,} reported cases in {location}. "
        + (info["symptoms"][:140] + "…" if info else "General information is not available yet.")
    )
    st.page_link("pages/1_🔎_Health_Information.py",
                 label=f"Open full details for {chosen} →", icon="🩺")

st.markdown("---")

# --------------------------------------------------------------------------
# 6. Awareness notice
# --------------------------------------------------------------------------
ui.medical_disclaimer()
ui.sidebar_footer()
