"""
utils/charts.py
---------------
Plotly chart builders used across the pages.

Each function takes a DataFrame and returns a figure, so the page files only
have to call st.plotly_chart(...). Charts return None when there is nothing to
plot, and the caller shows an empty-state message instead.
"""

import plotly.express as px
import plotly.graph_objects as go

PALETTE = ["#0f766e", "#0e7490", "#1d4ed8", "#7c3aed", "#db2777", "#ea580c", "#65a30d"]
SEVERITY_COLORS = {"Mild": "#16a34a", "Moderate": "#d97706", "Severe": "#dc2626"}

LAYOUT = dict(
    margin=dict(l=10, r=10, t=50, b=10),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13),
    hovermode="x unified",
)


def _finish(fig, title, xaxis=None, yaxis=None, hovermode="x unified"):
    layout = dict(LAYOUT)
    layout["hovermode"] = hovermode
    fig.update_layout(title=title, **layout)
    fig.update_xaxes(title=xaxis, showgrid=False)
    fig.update_yaxes(title=yaxis, gridcolor="#eef2f7")
    return fig


# --------------------------------------------------------------------------
# Case analytics
# --------------------------------------------------------------------------
def case_trend_line(daily_df, title="Reported cases over time"):
    """Line chart of daily reported cases."""
    if daily_df is None or daily_df.empty:
        return None
    fig = px.line(daily_df, x="case_date", y="cases", markers=False,
                  color_discrete_sequence=[PALETTE[0]])
    fig.update_traces(line=dict(width=2.5), fill="tozeroy",
                      fillcolor="rgba(15,118,110,0.12)")
    return _finish(fig, title, "Date", "Reported cases")


def multi_condition_trend(cases_df, conditions, title="Condition trends"):
    """Overlaid daily trend lines for several conditions."""
    if cases_df is None or cases_df.empty or not conditions:
        return None
    df = cases_df[cases_df["condition"].isin(conditions)].copy()
    if df.empty:
        return None
    grouped = (
        df.groupby([df["case_date"].dt.date, "condition"])
        .size().reset_index(name="cases")
    )
    grouped.columns = ["case_date", "condition", "cases"]
    fig = px.line(grouped, x="case_date", y="cases", color="condition",
                  color_discrete_sequence=PALETTE)
    fig.update_traces(line=dict(width=2.2))
    return _finish(fig, title, "Date", "Reported cases")


def condition_bar(dist_df, title="Most reported conditions"):
    """Horizontal bar chart of cases per condition."""
    if dist_df is None or dist_df.empty:
        return None
    df = dist_df.sort_values("cases")
    fig = px.bar(df, x="cases", y="condition", orientation="h",
                 color="cases", color_continuous_scale="Teal", text="cases")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(coloraxis_showscale=False)
    return _finish(fig, title, "Reported cases", None, hovermode="closest")


def hospital_bar(dist_df, title="Hospital-wise distribution"):
    """Cases per hospital."""
    if dist_df is None or dist_df.empty:
        return None
    df = dist_df.sort_values("cases")
    fig = px.bar(df, x="cases", y="hospital_name", orientation="h",
                 color_discrete_sequence=[PALETTE[1]], text="cases")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finish(fig, title, "Reported cases", None, hovermode="closest")


def age_bar(age_df, title="Age-group distribution"):
    if age_df is None or age_df.empty or age_df["cases"].sum() == 0:
        return None
    fig = px.bar(age_df, x="age_band", y="cases",
                 color_discrete_sequence=[PALETTE[2]], text="cases")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finish(fig, title, "Age group", "Reported cases", hovermode="closest")


def severity_pie(sev_df, title="Severity distribution"):
    if sev_df is None or sev_df.empty or sev_df["cases"].sum() == 0:
        return None
    fig = px.pie(sev_df, names="severity", values="cases", hole=0.55,
                 color="severity", color_discrete_map=SEVERITY_COLORS)
    fig.update_traces(textinfo="percent+label")
    return _finish(fig, title, None, None, hovermode="closest")


def gender_pie(gender_df, title="Gender distribution"):
    if gender_df is None or gender_df.empty or gender_df["cases"].sum() == 0:
        return None
    df = gender_df[gender_df["cases"] > 0]
    fig = px.pie(df, names="gender", values="cases", hole=0.55,
                 color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent+label")
    return _finish(fig, title, None, None, hovermode="closest")


# --------------------------------------------------------------------------
# Crowd analytics
# --------------------------------------------------------------------------
def crowd_history_line(queue_df, title="Reported crowd history"):
    """Patients waiting and waiting time over time (dual series)."""
    if queue_df is None or queue_df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=queue_df["recorded_at"], y=queue_df["patients_waiting"],
        name="Patients waiting", mode="lines",
        line=dict(color=PALETTE[0], width=2.2),
        fill="tozeroy", fillcolor="rgba(15,118,110,0.10)",
    ))
    fig.add_trace(go.Scatter(
        x=queue_df["recorded_at"], y=queue_df["estimated_waiting_minutes"],
        name="Waiting time (min)", mode="lines",
        line=dict(color=PALETTE[3], width=1.8, dash="dot"), yaxis="y2",
    ))
    fig.update_layout(
        yaxis2=dict(title="Waiting time (min)", overlaying="y", side="right",
                    showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return _finish(fig, title, "Recorded at", "Patients waiting")


def hourly_pattern_bar(hourly_df, title="Typical crowd by hour of day"):
    """Average patients waiting per hour — reveals busiest/quietest times."""
    if hourly_df is None or hourly_df.empty:
        return None
    df = hourly_df.copy()
    df["label"] = df["hour"].apply(lambda h: f"{int(h):02d}:00")
    fig = px.bar(df, x="label", y="avg_patients",
                 color="avg_patients", color_continuous_scale="Teal")
    fig.update_layout(coloraxis_showscale=False)
    return _finish(fig, title, "Hour of day", "Average patients waiting",
                   hovermode="closest")


def crowd_comparison_bar(latest_df, title="Current reported crowd by hospital"):
    """Side-by-side comparison of the latest reported crowd."""
    if latest_df is None or latest_df.empty:
        return None
    df = latest_df.dropna(subset=["patients_waiting"]).copy()
    if df.empty:
        return None
    df = df.sort_values("patients_waiting")
    fig = px.bar(df, x="patients_waiting", y="hospital_name", orientation="h",
                 color="status",
                 color_discrete_map={"Low": "#16a34a", "Moderate": "#d97706",
                                     "High": "#dc2626", "Unknown": "#94a3b8"},
                 text="patients_waiting")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finish(fig, title, "Patients waiting", None, hovermode="closest")


def prediction_curve(curve_df, title="Predicted crowd through the day"):
    """Predicted patients waiting across the operating hours of a day."""
    if curve_df is None or curve_df.empty:
        return None
    df = curve_df.copy()
    df["label"] = df["hour"].apply(lambda h: f"{int(h):02d}:00")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["label"], y=df["predicted_patients_waiting"],
        mode="lines+markers", name="Predicted patients waiting",
        line=dict(color=PALETTE[2], width=2.6, dash="dash"),
        marker=dict(size=7),
    ))
    return _finish(fig, title, "Hour", "Predicted patients waiting")


def predicted_vs_actual(holdout_df, hospital_name=None,
                        title="Model check: predicted vs actual (hold-out period)"):
    """
    Compares the model's predictions against the actual recorded values on the
    most recent slice of history that the model was NOT trained on.
    """
    if holdout_df is None or holdout_df.empty:
        return None
    df = holdout_df.copy()
    if hospital_name and "hospital_name" in df.columns:
        df = df[df["hospital_name"] == hospital_name]
    if df.empty:
        return None
    df = df.sort_values("recorded_at")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["recorded_at"], y=df["actual_patients_waiting"],
        mode="lines", name="Actual reported",
        line=dict(color=PALETTE[0], width=2.4),
    ))
    fig.add_trace(go.Scatter(
        x=df["recorded_at"], y=df["predicted_patients_waiting"],
        mode="lines", name="Model prediction",
        line=dict(color=PALETTE[4], width=2.0, dash="dot"),
    ))
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return _finish(fig, title, "Recorded at", "Patients waiting")
