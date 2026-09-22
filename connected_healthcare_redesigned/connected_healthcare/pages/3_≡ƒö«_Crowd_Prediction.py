"""
pages/3_🔮_Crowd_Prediction.py
------------------------------
Machine-learning crowd prediction.

Everything on this page is clearly labelled as a PREDICTION derived from
historical/demo data. The current reported crowd is shown alongside it so the
two are never confused.

The model's internal details (algorithm comparison, feature importance,
hold-out validation) are kept for the AI/ML project demonstration, but live
inside a collapsed "Technical details" section so a normal visitor is never
shown model jargon by default.
"""

from datetime import datetime, timedelta

import streamlit as st

import data_service
from config import MIN_ROWS_FOR_PREDICTION, OPERATING_HOURS
from utils import charts, ui
from utils.analysis_utils import annotate_crowd_status, crowd_status, describe_time_ago
from utils.database_utils import save_prediction

ui.setup_page("Crowd Prediction", icon="🔮")
ui.hero("Crowd Prediction • Estimated from historical reported data")

location = ui.location_selector()
version = data_service.data_version()
ui.demo_badge()

st.warning(
    "**Predicted values are not live hospital information.** They are "
    "statistical estimates based on historical demo records, and have not "
    "been validated against real hospital operations."
)

latest_df = annotate_crowd_status(data_service.latest_queue(location, version))
if latest_df is None or latest_df.empty:
    ui.empty_state(f"No hospitals are registered for {location} yet.")
    ui.sidebar_footer()
    st.stop()

# --------------------------------------------------------------------------
# Train (or reuse) the model for this location
# --------------------------------------------------------------------------
model, error = data_service.crowd_model(location, version)

if model is None:
    ui.empty_state(
        "Prediction is currently unavailable because there is not enough historical data.",
        f"At least {MIN_ROWS_FOR_PREDICTION} historical queue records are "
        "required. Add more updates from the 🔐 Admin page, or reseed the demo data.",
    )
    ui.sidebar_footer()
    st.stop()

# --------------------------------------------------------------------------
# Prediction inputs
# --------------------------------------------------------------------------
st.markdown("## 🔮 Predict Hospital Crowd")

hospital_names = latest_df["hospital_name"].tolist()
col_h, col_d, col_t = st.columns([2, 1, 1])

with col_h:
    selected_name = st.selectbox("Hospital", hospital_names, key="predict_hospital")
with col_d:
    target_date = st.date_input("Date", value=datetime.now().date(),
                                min_value=datetime.now().date() - timedelta(days=7),
                                max_value=datetime.now().date() + timedelta(days=14))
with col_t:
    default_hour = min(max(datetime.now().hour + 2, OPERATING_HOURS[0]), OPERATING_HOURS[-1])
    target_hour = st.selectbox(
        "Time", OPERATING_HOURS,
        index=OPERATING_HOURS.index(default_hour) if default_hour in OPERATING_HOURS else 0,
        format_func=lambda h: f"{h:02d}:00",
    )

selected = latest_df[latest_df["hospital_name"] == selected_name].iloc[0]
hospital_id = int(selected["hospital_id"])
target_dt = datetime.combine(target_date, datetime.min.time()).replace(hour=int(target_hour))

try:
    prediction = model.predict(hospital_id, target_dt)
except Exception as exc:
    ui.empty_state(f"No prediction is available for {selected_name}.", str(exc))
    ui.sidebar_footer()
    st.stop()

# --------------------------------------------------------------------------
# Current reported vs predicted — shown side by side, clearly separated
# --------------------------------------------------------------------------
st.markdown("### Current reported vs predicted")

current_col, predicted_col = st.columns(2)

with current_col:
    st.markdown("#### 🟦 Current / Reported")
    has_current = selected["patients_waiting"] == selected["patients_waiting"] \
        and selected["patients_waiting"] is not None
    if has_current:
        ui.metric_card("Current reported crowd",
                       f"{int(selected['patients_waiting'])} patients waiting",
                       f"Updated {describe_time_ago(selected['recorded_at'])}")
        st.markdown("")
        ui.metric_card("Reported waiting time",
                       f"{int(selected['estimated_waiting_minutes'])} minutes",
                       "Last value submitted by hospital staff")
    else:
        ui.metric_card("Current reported crowd", "Not reported",
                       "No staff update submitted yet")

with predicted_col:
    st.markdown("#### 🟪 Predicted (estimate)")
    ui.metric_card(
        f"Expected around {target_dt.strftime('%d %b, %I:%M %p')}",
        f"{prediction['predicted_patients_waiting']} patients waiting",
        f"Status estimate: {crowd_status(prediction['predicted_patients_waiting'])}",
    )
    st.markdown("")
    ui.metric_card("Predicted waiting time",
                   f"~{prediction['predicted_waiting_minutes']} minutes",
                   "Prediction based on historical data.")

ui.prediction_disclaimer()

if st.button("💾 Save this prediction", help="Stores the prediction so it can be "
                                            "compared with the actual value later"):
    try:
        save_prediction(hospital_id, target_dt,
                        prediction["predicted_patients_waiting"],
                        prediction["predicted_waiting_minutes"])
        data_service.refresh()
        st.success("Prediction saved to the database.")
    except Exception as exc:
        st.error(f"The prediction could not be saved: {exc}")

st.markdown("---")

# --------------------------------------------------------------------------
# Predicted curve for the whole day
# --------------------------------------------------------------------------
st.markdown("### 📈 Predicted Crowd Through the Day")
ui.chart_note(f"Expected crowd for {selected_name} across the day, based on historical patterns.")

curve = model.predict_day_curve(hospital_id, target_date, OPERATING_HOURS)
fig = charts.prediction_curve(
    curve, title=f"{selected_name} — predicted crowd on {target_date.strftime('%d %b %Y')}"
)
if fig:
    st.plotly_chart(fig, use_container_width=True)
    if not curve.empty:
        quietest = curve.loc[curve["predicted_patients_waiting"].idxmin()]
        busiest = curve.loc[curve["predicted_patients_waiting"].idxmax()]
        st.caption(
            f"Expected quietest around {int(quietest['hour']):02d}:00 "
            f"(~{int(quietest['predicted_patients_waiting'])} waiting), busiest around "
            f"{int(busiest['hour']):02d}:00 (~{int(busiest['predicted_patients_waiting'])} waiting). "
            "Prediction based on historical data."
        )
else:
    ui.empty_state("A day-long prediction curve is not available for this hospital.")

st.markdown("---")

# --------------------------------------------------------------------------
# Model transparency — kept for the project demonstration, hidden by default
# --------------------------------------------------------------------------
with st.expander("🧪 Technical details (for project demonstration)", expanded=False):
    st.caption(
        "This section is intended for the project viva/demonstration. Normal "
        "users do not need this information to use the platform."
    )

    tab_check, tab_models, tab_features, tab_saved = st.tabs([
        "✅ Predicted vs Actual", "📊 Model Comparison", "🔧 Features", "🗂️ Saved Predictions",
    ])

    with tab_check:
        fig = charts.predicted_vs_actual(model.holdout, hospital_name=selected_name)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "The model was trained on older records and tested on this most recent "
                "period, which it had not seen during training."
            )
        else:
            ui.empty_state("No hold-out comparison is available for this hospital.")

    with tab_models:
        st.dataframe(model.metrics_table(), use_container_width=True, hide_index=True)
        st.caption(
            "Two algorithms (Random Forest and Linear Regression) are trained and "
            "compared on a chronological hold-out split. The model with the lower "
            "mean absolute error (MAE) is used for predictions. "
            "These scores describe performance on demo data only."
        )

    with tab_features:
        importance = model.feature_importance()
        if importance.empty:
            st.write("Feature importances are available only for the tree-based model.")
        else:
            importance.columns = ["Feature", "Importance"]
            st.dataframe(importance, use_container_width=True, hide_index=True)
        st.markdown(
            """
            **Inputs used by the model**

            - Hour of the day (including a cyclical encoding)
            - Day of the week and weekend indicator
            - Day of the month
            - The hospital itself (one-hot encoded)
            - That hospital's historical average crowd, overall and at that hour

            Only information that is genuinely known in advance is used, so the model
            is not accidentally shown the answer during training.
            """
        )
        st.caption(
            f"Trained on {model.training_rows:,} queue records for {location}, "
            f"up to {model.trained_until.strftime('%d %b %Y, %I:%M %p')}."
        )

    with tab_saved:
        saved = data_service.saved_predictions(version, location=location)
        if saved is None or saved.empty:
            ui.empty_state("No predictions have been saved yet.")
        else:
            display = saved.copy()
            display["predicted_for"] = display["predicted_for"].dt.strftime("%d %b %Y, %I:%M %p")
            display["created_at"] = display["created_at"].dt.strftime("%d %b %Y, %I:%M %p")
            display = display[["hospital_name", "predicted_for",
                               "predicted_patients_waiting", "predicted_waiting_minutes",
                               "created_at"]]
            display.columns = ["Hospital", "Predicted for", "Predicted patients waiting",
                               "Predicted waiting (min)", "Generated at"]
            st.dataframe(display, use_container_width=True, hide_index=True)

st.markdown("---")
st.info(
    "Predictions describe expected crowd levels only. They are not medical "
    "advice and must not be used to decide whether to seek care. For "
    "emergencies, seek appropriate emergency medical care."
)
ui.sidebar_footer()
