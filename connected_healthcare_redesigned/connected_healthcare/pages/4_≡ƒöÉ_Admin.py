"""
pages/4_🔐_Admin.py
-------------------
Administration / hospital-staff section.

This is NOT for normal public users. It allows demo administrators to submit
new crowd updates and reported cases, which then appear on the public pages.

Authentication note: this is a simple demo login intended for a college
prototype. It is deliberately NOT presented as enterprise-grade security —
credentials live in config.py and there is no user management, hashing,
session expiry or audit trail.
"""

from datetime import datetime

import streamlit as st

import data_service
from config import (
    AGE_BAND_LABELS,
    DEMO_ADMIN_PASSWORD,
    DEMO_ADMIN_USERNAME,
    GENDERS,
    SEVERITY_LEVELS,
)
from utils import ui
from utils.analysis_utils import crowd_status, describe_time_ago
from utils.database_utils import (
    add_hospital,
    insert_case_records,
    insert_queue_record,
    upsert_health_information,
)

ui.setup_page("Admin", icon="🔐")
ui.hero("Admin / Hospital Staff • Data entry for the prototype")

# --------------------------------------------------------------------------
# Demo authentication
# --------------------------------------------------------------------------
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

if not st.session_state["admin_authenticated"]:
    st.info(
        "This section is intended for authorised hospital staff. "
        "A simple demo login is used for this college prototype — it is not "
        "enterprise-level authentication."
    )
    with st.form("admin_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if username == DEMO_ADMIN_USERNAME and password == DEMO_ADMIN_PASSWORD:
            st.session_state["admin_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect demo credentials.")

    with st.expander("Demo credentials (prototype only)"):
        st.code(f"username: {DEMO_ADMIN_USERNAME}\npassword: {DEMO_ADMIN_PASSWORD}")
    st.stop()

# --------------------------------------------------------------------------
# Signed in
# --------------------------------------------------------------------------
top_left, top_right = st.columns([4, 1])
with top_left:
    st.success("Signed in as demo administrator.")
with top_right:
    if st.button("Sign out", use_container_width=True):
        st.session_state["admin_authenticated"] = False
        st.rerun()

version = data_service.data_version()
all_hospitals = data_service.hospitals(None, version)

if all_hospitals.empty:
    st.warning("No hospitals exist yet. Add one below or reseed the demo data.")

tab_queue, tab_cases, tab_info, tab_hospital, tab_db = st.tabs([
    "🏥 Update Hospital Crowd", "🩺 Report Cases", "📚 Health Information",
    "➕ Add Hospital", "🗄️ Database",
])

# --------------------------------------------------------------------------
# 1. Crowd update — appends a NEW timestamped record
# --------------------------------------------------------------------------
with tab_queue:
    st.markdown("### Update current hospital crowd")
    st.caption(
        "Each submission adds a new timestamped record. Existing history is "
        "never overwritten — that history is what powers the trend charts and "
        "the prediction model."
    )

    if all_hospitals.empty:
        ui.empty_state("Add a hospital first.")
    else:
        options = {
            f"{row.hospital_name} — {row.location}": int(row.hospital_id)
            for row in all_hospitals.itertuples()
        }
        with st.form("queue_update_form"):
            choice = st.selectbox("Hospital", list(options.keys()))
            col_a, col_b = st.columns(2)
            with col_a:
                patients = st.number_input("Current patients waiting",
                                           min_value=0, max_value=500, value=20, step=1)
            with col_b:
                minutes = st.number_input("Estimated waiting time (minutes)",
                                          min_value=0, max_value=600, value=35, step=5)

            use_now = st.checkbox("Use the current date and time", value=True)
            col_c, col_d = st.columns(2)
            with col_c:
                record_date = st.date_input("Record date", value=datetime.now().date(),
                                            disabled=use_now)
            with col_d:
                record_time = st.time_input("Record time", value=datetime.now().time(),
                                            disabled=use_now)

            submitted = st.form_submit_button("Submit crowd update",
                                              use_container_width=True)

        if submitted:
            recorded_at = (
                datetime.now() if use_now
                else datetime.combine(record_date, record_time)
            )
            try:
                insert_queue_record(options[choice], int(patients), int(minutes),
                                    recorded_at=recorded_at)
                data_service.refresh()
                st.success(
                    f"Recorded {int(patients)} patients waiting "
                    f"({crowd_status(int(patients))} crowd) at "
                    f"{recorded_at.strftime('%d %b %Y, %I:%M %p')}. "
                    "The public dashboard now shows this value."
                )
            except Exception as exc:
                st.error(f"The update could not be saved: {exc}")

        # Show what the public dashboard is currently displaying
        st.markdown("#### Latest reported values (what the public sees)")
        for location in sorted(all_hospitals["location"].unique()):
            latest = data_service.latest_queue(location, data_service.data_version())
            if latest.empty:
                continue
            st.markdown(f"**{location}**")
            display = latest.copy()
            display["Status"] = display["patients_waiting"].apply(
                lambda v: crowd_status(v) if v == v else "Unknown"
            )
            display["Last updated"] = display["recorded_at"].apply(describe_time_ago)
            display = display[["hospital_name", "patients_waiting",
                               "estimated_waiting_minutes", "Status", "Last updated"]]
            display.columns = ["Hospital", "Patients waiting",
                               "Estimated waiting (min)", "Status", "Last updated"]
            st.dataframe(display, use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------
# 2. Report cases
# --------------------------------------------------------------------------
with tab_cases:
    st.markdown("### Report health-condition cases")
    st.caption(
        "Only anonymous attributes are recorded: condition, age, gender, "
        "severity and date. Never enter names, contact details, addresses or "
        "medical identifiers."
    )

    if all_hospitals.empty:
        ui.empty_state("Add a hospital first.")
    else:
        options = {
            f"{row.hospital_name} — {row.location}": int(row.hospital_id)
            for row in all_hospitals.itertuples()
        }
        known_conditions = data_service.all_known_conditions(version)

        with st.form("case_form"):
            choice = st.selectbox("Hospital", list(options.keys()), key="case_hospital")

            col_a, col_b = st.columns(2)
            with col_a:
                condition_choice = st.selectbox(
                    "Condition", known_conditions + ["➕ New condition…"]
                )
                new_condition = st.text_input("New condition name",
                                              placeholder="Only if 'New condition' is selected")
            with col_b:
                severity = st.selectbox("Severity", SEVERITY_LEVELS)
                count = st.number_input("Number of cases", min_value=1, max_value=100,
                                        value=1, step=1)

            col_c, col_d, col_e = st.columns(3)
            with col_c:
                age = st.number_input("Patient age", min_value=0, max_value=120, value=30)
            with col_d:
                gender = st.selectbox("Gender", GENDERS)
            with col_e:
                case_date = st.date_input("Case date", value=datetime.now().date())

            submitted = st.form_submit_button("Save case record(s)",
                                              use_container_width=True)

        if submitted:
            condition = (new_condition.strip()
                         if condition_choice == "➕ New condition…" else condition_choice)
            if not condition:
                st.error("Please provide a condition name.")
            else:
                try:
                    saved = insert_case_records(
                        options[choice], condition, severity, count=int(count),
                        age=int(age), gender=gender, case_date=case_date,
                    )
                    data_service.refresh()
                    st.success(
                        f"Saved {saved} reported case record(s) for {condition}. "
                        "They now appear in the dashboard and Health Explorer."
                    )
                    if not data_service.health_information(
                        condition, data_service.data_version()
                    ):
                        st.info(
                            f"No general health information exists for {condition} yet. "
                            "You can add it in the 📚 Health Information tab."
                        )
                except Exception as exc:
                    st.error(f"The case record could not be saved: {exc}")

        st.caption(f"Age bands used in analysis: {', '.join(AGE_BAND_LABELS)}")

# --------------------------------------------------------------------------
# 3. Health information
# --------------------------------------------------------------------------
with tab_info:
    st.markdown("### Add or update general health information")
    st.caption(
        "This content is educational and general. It must not diagnose, must not "
        "recommend specific medication, and should direct people to qualified "
        "healthcare professionals."
    )

    known_conditions = data_service.all_known_conditions(version)
    target = st.selectbox("Condition", known_conditions + ["➕ New condition…"],
                          key="info_condition")
    if target == "➕ New condition…":
        target_name = st.text_input("New condition name", key="info_new_name")
        existing = None
    else:
        target_name = target
        existing = data_service.health_information(target, version)

    with st.form("health_info_form"):
        symptoms = st.text_area("General symptoms",
                                value=(existing or {}).get("symptoms", ""), height=110)
        prevention = st.text_area("General prevention information",
                                  value=(existing or {}).get("prevention", ""), height=110)
        seek_help = st.text_area("When to seek professional medical help",
                                 value=(existing or {}).get("when_to_seek_help", ""),
                                 height=110)
        submitted = st.form_submit_button("Save health information",
                                          use_container_width=True)

    if submitted:
        if not target_name or not target_name.strip():
            st.error("Please provide a condition name.")
        elif not (symptoms.strip() and prevention.strip() and seek_help.strip()):
            st.error("All three information fields are required.")
        else:
            try:
                upsert_health_information(target_name.strip(), symptoms.strip(),
                                          prevention.strip(), seek_help.strip())
                data_service.refresh()
                st.success(f"Health information saved for {target_name.strip()}.")
            except Exception as exc:
                st.error(f"The information could not be saved: {exc}")

# --------------------------------------------------------------------------
# 4. Add hospital
# --------------------------------------------------------------------------
with tab_hospital:
    st.markdown("### Register a new hospital")
    st.caption(
        "A new location typed here becomes available in the public location "
        "selector as soon as the hospital is saved."
    )
    with st.form("hospital_form"):
        name = st.text_input("Hospital name")
        existing_locations = data_service.locations(version)
        location_choice = st.selectbox("Location",
                                       existing_locations + ["➕ New location…"])
        new_location = st.text_input("New location name",
                                     placeholder="Only if 'New location' is selected")
        submitted = st.form_submit_button("Add hospital", use_container_width=True)

    if submitted:
        final_location = (new_location.strip()
                          if location_choice == "➕ New location…" else location_choice)
        if not name.strip() or not final_location:
            st.error("Both a hospital name and a location are required.")
        else:
            try:
                add_hospital(name.strip(), final_location)
                data_service.refresh()
                st.success(f"{name.strip()} has been added to {final_location}.")
            except Exception as exc:
                st.error(f"The hospital could not be added: {exc}")

# --------------------------------------------------------------------------
# 5. Database tools
# --------------------------------------------------------------------------
with tab_db:
    st.markdown("### Database status")
    summary = data_service.database_summary(data_service.data_version())

    cols = st.columns(len(summary))
    for col, (table, count) in zip(cols, summary.items()):
        with col:
            ui.metric_card(table.replace("_", " ").title(), f"{count:,}", "rows")

    st.markdown("")
    st.markdown("#### Demo data tools")
    st.caption(
        "Reseeding deletes every record and regenerates the synthetic demo "
        "dataset. Use it to reset the project before a demonstration."
    )

    confirm = st.checkbox("I understand this will delete all current records")
    if st.button("♻️ Reset and regenerate demo data", disabled=not confirm):
        try:
            from seed_data import reset_and_seed

            result = reset_and_seed()
            data_service.refresh()
            st.success(
                f"Demo data regenerated: {result['hospitals']} hospitals, "
                f"{result['cases']:,} case records, {result['queue_records']:,} "
                "queue records."
            )
        except Exception as exc:
            st.error(f"The demo data could not be regenerated: {exc}")

ui.sidebar_footer()
