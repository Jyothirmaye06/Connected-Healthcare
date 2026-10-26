
import sqlite3

import pandas as pd
import streamlit as st

from config import DB_PATH
from src.ui.common import language, render_footer, render_header

lang = language()
render_header("Hospital Dataset & Updates", "View staff-submitted hospital observations.")

st.caption("Data is loaded directly from the existing SQLite database.")

try:
    with sqlite3.connect(DB_PATH) as conn:
        total = pd.read_sql_query(
            "SELECT COUNT(*) AS total FROM hospital_crowd", conn
        ).iloc[0]["total"]

        hospitals = pd.read_sql_query(
            "SELECT id, name FROM hospitals ORDER BY name", conn
        )

        records = pd.read_sql_query(
            """
            SELECT
                hc.id,
                h.name AS hospital,
                hc.people_waiting,
                hc.waiting_minutes,
                hc.new_patients,
                hc.discharged_patients,
                hc.emergency_cases,
                hc.holiday,
                hc.special_event,
                hc.recorded_at
            FROM hospital_crowd hc
            JOIN hospitals h ON h.id = hc.hospital_id
            ORDER BY hc.id DESC
            """,
            conn,
        )

    st.metric("Total observations", int(total))

    selected = st.selectbox(
        "Filter by hospital",
        ["All hospitals"] + hospitals["name"].tolist(),
    )

    if selected != "All hospitals":
        records = records[records["hospital"] == selected]

    search = st.text_input("Search records or special events")
    if search:
        mask = records.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        records = records[mask]

    st.subheader("Hospital observations")
    st.write("Latest 100 hospital records")
    st.dataframe(records.head(100), use_container_width=True, hide_index=True)
    st.caption(f"Records displayed: {len(records)}")

    if st.button("Refresh dataset"):
        st.rerun()

except (sqlite3.Error, pd.errors.DatabaseError) as exc:
    st.error(f"Unable to load the dataset: {exc}")

render_footer()
