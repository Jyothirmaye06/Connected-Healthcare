import logging
import sqlite3
import time
import uuid

import pandas as pd
import plotly.express as px
import streamlit as st

from config import (
    ANOMALY_MODELS_PATH,
    CROWD_MODEL_PATH,
    DB_PATH,
    FEATURE_COLUMNS,
    PREDICTION_HORIZON_LABEL,
    WAITING_MODEL_PATH,
)
from src.anomaly_detection import load_anomaly_models
from src.data_access import get_all_crowd_data, get_health_cases_df, get_hospitals_df, get_connection
from src.hospital_intelligence import get_hospital_intelligence
from src.prediction import load_models
from src.simulation_schedule import (
    acquire_simulation_lease,
    release_simulation_lease,
    renew_simulation_lease,
    schedule_next_simulation_tick,
    simulate_selected_hospitals,
    simulation_tick_is_due,
)
from src.site_i18n import site_t
from src.synthetic_generator import simulate_next_observation
from src.staff_portal import get_observation_audit
from src.staff_accounts import (
    create_staff_account,
    set_staff_account_status,
)
from src.ui.common import language, render_footer, render_header, require_role

LOGGER = logging.getLogger(__name__)
lang = language()
user = require_role("admin")
render_header(site_t("admin", lang), site_t("technical_intro", lang))

tab_names = [
    site_t("system_status", lang),
    site_t("dataset", lang),
    site_t("ml_monitoring", lang),
    site_t("model_evaluation", lang),
    site_t("anomaly", lang),
    site_t("database", lang),
    site_t("simulation", lang),
]
tab_names.append("Staff Management")

(
    system_tab,
    data_tab,
    ml_tab,
    evaluation_tab,
    anomaly_tab,
    database_tab,
    simulation_tab,
    staff_tab,
) = st.tabs(tab_names)

with system_tab:
    st.subheader(site_t("system_status", lang))
    db_status = "Found" if DB_PATH.is_file() else "Missing"
    st.metric(site_t("database_file", lang), db_status)
    st.caption(f"{site_t('path', lang)}: {DB_PATH}")
    artifact_rows = []
    for label, artifact_path in (
        ("Crowd prediction", CROWD_MODEL_PATH),
        ("Waiting-time prediction", WAITING_MODEL_PATH),
        ("Hospital anomaly", ANOMALY_MODELS_PATH),
    ):
        artifact_rows.append({
            site_t("artifact", lang): label,
            site_t("path", lang): str(artifact_path),
            site_t("file_exists", lang): artifact_path.is_file(),
        })
    st.dataframe(pd.DataFrame(artifact_rows), use_container_width=True, hide_index=True)
    st.caption(f"Prediction horizon: {PREDICTION_HORIZON_LABEL}")
    st.caption("File existence alone is not treated as proof of model loading.")
    try:
        crowd_model, waiting_model = load_models()
        anomaly_models = load_anomaly_models()
        st.success(
            f"{site_t('loaded_models', lang)}: {type(crowd_model).__name__}, "
            f"{type(waiting_model).__name__}. Loaded anomaly models: {len(anomaly_models)}."
        )
    except (OSError, ValueError, KeyError, ImportError):
        LOGGER.exception("Unable to load one or more saved model artifacts.")
        st.error(site_t("load_failure", lang))

with data_tab:
    st.subheader(site_t("dataset", lang))
    try:
        crowd = get_all_crowd_data()
        cases = get_health_cases_df()
        hospitals = get_hospitals_df()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(site_t("crowd_observations", lang), len(crowd))
        c2.metric(site_t("health_records", lang), len(cases))
        c3.metric(site_t("hospital", lang), len(hospitals))
        c4.metric(site_t("tracked_conditions", lang), cases["condition"].nunique() if not cases.empty else 0)
        if not crowd.empty:
            selected = st.selectbox(
                "Facility filter",
                [site_t("all_facilities", lang)] + sorted(crowd["hospital"].unique().tolist()),
                key="admin_data_facility",
            )
            view = crowd if selected == site_t("all_facilities", lang) else crowd[crowd["hospital"] == selected]
            st.dataframe(view.sort_values("recorded_at", ascending=False), use_container_width=True, height=320)
            st.download_button(
                site_t("export_csv", lang),
                view.to_csv(index=False),
                file_name="hospital_observations.csv",
                mime="text/csv",
            )
        else:
            st.info(site_t("no_observations", lang))
    except sqlite3.Error:
        LOGGER.exception("Unable to read dataset for admin explorer.")
        st.error(site_t("unavailable", lang))

with ml_tab:
    st.subheader(site_t("ml_monitoring", lang))
    try:
        crowd_model, waiting_model = load_models()
        model_info = []
        for target, pipeline in (
            ("People waiting", crowd_model),
            ("Waiting time", waiting_model),
        ):
            estimator = pipeline.named_steps.get("model") if hasattr(pipeline, "named_steps") else pipeline
            params = estimator.get_params() if hasattr(estimator, "get_params") else {}
            model_info.append({
                site_t("prediction_target", lang): target,
                site_t("pipeline_type", lang): type(pipeline).__name__,
                site_t("estimator", lang): type(estimator).__name__,
                site_t("estimators", lang): params.get("n_estimators", site_t("not_exposed", lang)),
                site_t("features", lang): len(FEATURE_COLUMNS),
            })
        st.dataframe(pd.DataFrame(model_info), use_container_width=True, hide_index=True)
        st.code(", ".join(FEATURE_COLUMNS), language="text")
        rf_estimator = crowd_model.named_steps.get("model")
        if hasattr(rf_estimator, "feature_importances_"):
            importance = pd.DataFrame({
                site_t("feature_importance", lang): range(len(rf_estimator.feature_importances_)),
                "Importance": rf_estimator.feature_importances_,
            }).sort_values("Importance", ascending=False).head(15)
            fig = px.bar(importance, x="Importance", y=site_t("feature_importance", lang), orientation="h")
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
    except (OSError, ValueError, KeyError, AttributeError):
        LOGGER.exception("Unable to inspect loaded prediction models.")
        st.error("Saved prediction models could not be loaded or inspected.")

with evaluation_tab:
    st.subheader(site_t("model_evaluation", lang))
    st.warning(site_t("evaluation_disclaimer", lang))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{site_t('historical_crowd', lang)}**")
        st.dataframe(pd.DataFrame([
            {"Model": "Persistence baseline", "MAE": 5.95, "RMSE": 7.56, "R²": 0.715},
            {"Model": "Rolling 3-period mean", "MAE": 9.36, "RMSE": 11.74, "R²": 0.311},
            {"Model": "Linear regression", "MAE": 5.74, "RMSE": 7.34, "R²": 0.731},
            {"Model": "HistGradientBoosting", "MAE": 5.64, "RMSE": 7.24, "R²": 0.738},
            {"Model": "Random Forest", "MAE": 5.82, "RMSE": 7.38, "R²": 0.728},
        ]), use_container_width=True, hide_index=True)
    with col2:
        st.markdown(f"**{site_t('historical_waiting', lang)}**")
        st.dataframe(pd.DataFrame([
            {"Model": "Persistence baseline", "MAE": 8.13, "RMSE": 10.82, "R²": 0.234},
            {"Model": "Linear regression", "MAE": 6.22, "RMSE": 8.65, "R²": 0.511},
            {"Model": "HistGradientBoosting", "MAE": 6.45, "RMSE": 8.86, "R²": 0.487},
            {"Model": "Random Forest", "MAE": 6.29, "RMSE": 8.72, "R²": 0.503},
        ]), use_container_width=True, hide_index=True)

with anomaly_tab:
    st.subheader(site_t("anomaly", lang))
    try:
        hospitals = get_hospitals_df()
        if hospitals.empty:
            st.info(site_t("no_observations", lang))
        else:
            selected_hospital = st.selectbox(site_t("facility_diagnostics", lang), hospitals["name"].tolist())
            diagnostics = get_hospital_intelligence(selected_hospital)
            metrics = st.columns(4)
            metrics[0].metric("Isolation Forest score", diagnostics["anomaly_score"])
            metrics[1].metric(
                site_t("anomaly", lang),
                site_t("outlier", lang) if diagnostics["is_anomaly"] else site_t("not_flagged", lang),
            )
            metrics[2].metric("Crowd deviation", diagnostics["crowd_deviation"])
            metrics[3].metric("Operational status", diagnostics["status"])
            st.write(f"{site_t('reasons', lang)}:", "; ".join(diagnostics["reasons"]))
            st.caption("Isolation Forest detects statistical outliers; threshold status is rule-based, not diagnostic.")
    except (sqlite3.Error, OSError, ValueError, KeyError, IndexError):
        LOGGER.exception("Unable to calculate anomaly diagnostics.")
        st.error(site_t("unavailable", lang))

with database_tab:
    st.subheader(site_t("database", lang))
    try:
        conn = get_connection()
        try:
            table_rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            stats = []
            for row in table_rows:
                table_name = row["name"]
                count = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
                stats.append({"Table": table_name, "Rows": int(count)})
            latest = conn.execute("SELECT MAX(recorded_at) FROM hospital_crowd").fetchone()[0]
        finally:
            conn.close()
        st.caption(f"{site_t('database_path', lang)}: {DB_PATH}")
        st.caption(f"{site_t('latest_observation', lang)}: {latest or site_t('unavailable', lang)}")
        st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)
    except sqlite3.Error:
        LOGGER.exception("Unable to inspect database tables.")
        st.error(site_t("unavailable", lang))
    try:
        audit = get_observation_audit(user, limit=100)
        st.subheader(site_t("staff_audit", lang))
        st.dataframe(audit, use_container_width=True, hide_index=True)
    except (sqlite3.Error, PermissionError):
        LOGGER.exception("Unable to load staff submission audit.")
        st.warning(site_t("audit_after_first", lang))

with simulation_tab:
    st.subheader(site_t("simulation", lang))
    st.info(site_t("simulated_label", lang))
    try:
        hospitals = get_hospitals_df()
    except sqlite3.Error:
        LOGGER.exception("Unable to load hospitals for simulation controls.")
        st.error(site_t("unavailable", lang))
        hospitals = pd.DataFrame()

    if hospitals.empty:
        st.info(site_t("no_observations", lang))
    else:
        all_ids = hospitals["id"].astype(int).tolist()
        st.session_state.setdefault("simulation_status", "stopped")
        st.session_state.setdefault("simulation_owner_token", uuid.uuid4().hex)
        st.session_state.setdefault("simulation_hospital_ids", all_ids)
        st.session_state.setdefault("simulation_interval_seconds", 300)
        st.session_state.setdefault("simulation_next_tick_at", None)
        st.session_state.setdefault("simulation_last_results", [])
        st.session_state.setdefault("simulation_last_errors", [])
        interval_values = [60, 300, 900]
        interval = st.selectbox(
            site_t("interval", lang),
            interval_values,
            format_func=lambda value: f"{value // 60} {site_t('minute_s', lang)}",
            key="simulation_interval_seconds",
        )
        selected_ids = st.multiselect(
            site_t("selected_hospitals", lang),
            options=all_ids,
            default=[item for item in st.session_state["simulation_hospital_ids"] if item in all_ids],
            format_func=lambda item: (
                f"{hospitals.loc[hospitals['id'] == item, 'name'].iloc[0]} "
                f"({hospitals.loc[hospitals['id'] == item, 'location'].iloc[0]})"
            ),
            disabled=st.session_state["simulation_status"] == "running",
            key="simulation_selected_ids",
        )
        st.session_state["simulation_hospital_ids"] = selected_ids

        if st.session_state["simulation_status"] == "running":
            @st.fragment(run_every=interval)
            def scheduled_simulation_tick():
                now = time.monotonic()
                owner = st.session_state["simulation_owner_token"]
                if not renew_simulation_lease(owner, now, interval * 2 + 30):
                    st.session_state["simulation_status"] = "stopped"
                    st.session_state["simulation_next_tick_at"] = None
                    st.error(site_t("lease_expired", lang))
                    return
                if simulation_tick_is_due(
                    st.session_state["simulation_status"],
                    st.session_state["simulation_next_tick_at"],
                    now,
                ):
                    generated, errors = simulate_selected_hospitals(
                        st.session_state["simulation_hospital_ids"]
                    )
                    st.session_state["simulation_last_results"] = generated
                    st.session_state["simulation_last_errors"] = errors
                    st.session_state["simulation_next_tick_at"] = schedule_next_simulation_tick(
                        time.monotonic(), interval
                    )
                    for error in errors:
                        st.error(error)
                    if generated:
                        st.success(f"Added {len(generated)} simulated hospital observation(s).")
                st.metric(site_t("simulation", lang), site_t("status_running", lang))
                if st.session_state["simulation_last_results"]:
                    last = st.session_state["simulation_last_results"][-1]
                    st.caption(f"{site_t('latest', lang)}: {last['hospital_name']} · {last['recorded_at']}")

            scheduled_simulation_tick()
        else:
            st.metric(
                site_t("simulation", lang),
                site_t(f"status_{st.session_state['simulation_status']}", lang),
            )

        control_cols = st.columns(3)
        if control_cols[0].button(site_t("start", lang), disabled=not selected_ids):
            token = st.session_state["simulation_owner_token"]
            now = time.monotonic()
            if acquire_simulation_lease(token, now, interval * 2 + 30):
                st.session_state["simulation_status"] = "running"
                st.session_state["simulation_next_tick_at"] = schedule_next_simulation_tick(now, interval)
                st.session_state["simulation_last_errors"] = []
                st.rerun()
            else:
                st.error(site_t("lease_conflict", lang))
        if control_cols[1].button(
            site_t("pause", lang),
            disabled=st.session_state["simulation_status"] != "running",
        ):
            release_simulation_lease(st.session_state["simulation_owner_token"])
            st.session_state["simulation_status"] = "paused"
            st.rerun()
        if control_cols[2].button(
            site_t("stop", lang),
            disabled=st.session_state["simulation_status"] == "stopped",
        ):
            release_simulation_lease(st.session_state["simulation_owner_token"])
            st.session_state["simulation_status"] = "stopped"
            st.session_state["simulation_next_tick_at"] = None
            st.rerun()
        st.caption(site_t("tick_caption", lang))
        one_time_hospital = st.selectbox(
            site_t("manual_simulation", lang),
            all_ids,
            format_func=lambda item: hospitals.loc[hospitals["id"] == item, "name"].iloc[0],
            disabled=st.session_state["simulation_status"] == "running",
            key="manual_simulation_hospital",
        )
        if st.button(site_t("generate_observation", lang), disabled=st.session_state["simulation_status"] == "running"):
            generated, errors = simulate_selected_hospitals([one_time_hospital])
            for error in errors:
                st.error(error)
            if generated:
                st.success(f"Added {generated[0]['hospital_name']} observation at {generated[0]['recorded_at']}.")
                st.rerun()
        if st.button(site_t("generate_day", lang), disabled=st.session_state["simulation_status"] == "running"):
            progress = st.progress(0)
            generated_count = 0
            for index in range(12):
                try:
                    simulate_next_observation(one_time_hospital)
                except (sqlite3.Error, ValueError) as error:
                    st.error(site_t("partial_day", lang).format(count=generated_count, error=error))
                    break
                generated_count += 1
                progress.progress((index + 1) / 12)
            if generated_count == 12:
                st.success(site_t("day_complete", lang))
                st.rerun()

render_footer()
with staff_tab:
    st.subheader("Staff Management")
    st.caption(
        "Create staff accounts, assign hospitals, and approve or suspend access."
    )

    try:
        conn = get_connection()
        try:
            staff_rows = conn.execute(
                """
                SELECT
                    s.id,
                    s.username,
                    s.hospital_id,
                    h.name AS hospital_name,
                    s.status,
                    s.created_by,
                    s.created_at,
                    s.updated_at
                FROM staff_accounts AS s
                JOIN hospitals AS h ON h.id = s.hospital_id
                ORDER BY s.created_at DESC, s.username
                """
            ).fetchall()
        finally:
            conn.close()

        if staff_rows:
            st.dataframe(
                pd.DataFrame([dict(row) for row in staff_rows]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No staff accounts have been created yet.")

    except sqlite3.Error:
        LOGGER.exception("Unable to load staff accounts.")
        st.error("Could not load staff accounts.")

    st.divider()
    st.subheader("Create a staff account")

    try:
        hospitals_df = get_hospitals_df()

        if hospitals_df.empty:
            st.warning("Create or configure a hospital before adding staff.")
        else:
            hospital_options = {
                f"{row['name']} (ID: {int(row['id'])})": int(row["id"])
                for _, row in hospitals_df.iterrows()
            }

            with st.form("create_staff_account_form"):
                new_username = st.text_input(
                    "Staff username",
                    max_chars=80,
                )
                new_password = st.text_input(
                    "Temporary password (minimum 12 characters)",
                    type="password",
                )
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                )
                selected_hospital_label = st.selectbox(
                    "Assign hospital",
                    list(hospital_options.keys()),
                )

                create_submitted = st.form_submit_button(
                    "Create staff account",
                    use_container_width=True,
                )

            if create_submitted:
                if new_password != confirm_password:
                    st.error("The passwords do not match.")
                else:
                    try:
                        create_staff_account(
                            username=new_username,
                            password=new_password,
                            hospital_id=hospital_options[
                                selected_hospital_label
                            ],
                            created_by=user,
                        )
                        st.success(
                            "Staff account created as pending. "
                            "Approve it below before the staff member can sign in."
                        )
                        st.rerun()
                    except (ValueError, PermissionError) as exc:
                        st.error(str(exc))
                    except sqlite3.Error:
                        LOGGER.exception("Unable to create staff account.")
                        st.error("Could not create the account.")

    except sqlite3.Error:
        LOGGER.exception("Unable to load hospitals for staff creation.")
        st.error("Could not load hospital assignments.")

    st.divider()
    st.subheader("Approve or suspend staff")

    try:
        conn = get_connection()
        try:
            action_rows = conn.execute(
                """
                SELECT username, status, hospital_id
                FROM staff_accounts
                ORDER BY username
                """
            ).fetchall()
        finally:
            conn.close()

        if action_rows:
            account_options = {
                f"{row['username']} — {row['status']} — Hospital ID {row['hospital_id']}":
                    row["username"]
                for row in action_rows
            }

            selected_account_label = st.selectbox(
                "Select staff account",
                list(account_options.keys()),
                key="staff_status_account",
            )
            selected_username = account_options[selected_account_label]

            selected_row = next(
                row for row in action_rows
                if row["username"] == selected_username
            )
            current_status = selected_row["status"]

            status_options = ["pending", "active", "suspended"]
            new_status = st.selectbox(
                "New account status",
                status_options,
                index=status_options.index(current_status),
                key="staff_new_status",
            )

            if st.button(
                "Save account status",
                type="primary",
                key="save_staff_status",
            ):
                try:
                    set_staff_account_status(
                        username=selected_username,
                        status=new_status,
                        actor=user,
                    )
                    st.success(
                        f"Updated {selected_username} to {new_status}."
                    )
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))
                except sqlite3.Error:
                    LOGGER.exception("Unable to update staff account status.")
                    st.error("Could not update the account status.")
        else:
            st.info("Create a staff account first to manage its status.")

    except sqlite3.Error:
        LOGGER.exception("Unable to load accounts for status management.")
        st.error("Could not load staff account statuses.")
