"""
utils/analysis_utils.py
-----------------------
Pure analysis functions operating on DataFrames produced by database_utils.

No Streamlit, no SQL, no plotting — which keeps the numbers testable and lets
the same helpers be reused by every page.
"""

from datetime import datetime

import numpy as np
import pandas as pd

from config import (
    AGE_BANDS,
    AGE_BAND_LABELS,
    CROWD_THRESHOLDS,
    GENDERS,
    MIN_CASES_FOR_TREND,
    SEVERITY_LEVELS,
    TREND_WINDOW_DAYS,
)


# --------------------------------------------------------------------------
# Age handling
# --------------------------------------------------------------------------
def age_to_band(age):
    """Map a numeric age to one of the configured age bands."""
    try:
        age = int(age)
    except (TypeError, ValueError):
        return "Unknown"
    for label, low, high in AGE_BANDS:
        if low <= age <= high:
            return label
    return "Unknown"


def add_age_band(cases_df):
    """Return a copy of the cases frame with an `age_band` column added."""
    if cases_df is None or cases_df.empty:
        return pd.DataFrame(columns=list(getattr(cases_df, "columns", [])) + ["age_band"])
    out = cases_df.copy()
    out["age_band"] = out["age"].apply(age_to_band)
    return out


# --------------------------------------------------------------------------
# Headline KPIs
# --------------------------------------------------------------------------
def overview_metrics(cases_df, hospitals_df):
    """
    Headline numbers for the homepage cards.

    Every value is computed from the data passed in — nothing is hard-coded.
    """
    metrics = {
        "total_cases": 0,
        "hospital_count": 0 if hospitals_df is None else int(len(hospitals_df)),
        "top_condition": "No data",
        "top_condition_cases": 0,
        "top_age_band": "No data",
        "top_age_band_cases": 0,
    }
    if cases_df is None or cases_df.empty:
        return metrics

    metrics["total_cases"] = int(len(cases_df))

    condition_counts = cases_df["condition"].value_counts()
    if not condition_counts.empty:
        metrics["top_condition"] = str(condition_counts.index[0])
        metrics["top_condition_cases"] = int(condition_counts.iloc[0])

    banded = add_age_band(cases_df)
    band_counts = banded["age_band"].value_counts()
    if not band_counts.empty:
        metrics["top_age_band"] = str(band_counts.index[0])
        metrics["top_age_band_cases"] = int(band_counts.iloc[0])

    return metrics


# --------------------------------------------------------------------------
# Distributions
# --------------------------------------------------------------------------
def condition_distribution(cases_df, top_n=None):
    """Cases per condition, highest first."""
    if cases_df is None or cases_df.empty:
        return pd.DataFrame(columns=["condition", "cases"])
    out = (
        cases_df.groupby("condition").size()
        .reset_index(name="cases")
        .sort_values("cases", ascending=False)
        .reset_index(drop=True)
    )
    return out.head(top_n) if top_n else out


def hospital_distribution(cases_df):
    """Cases per hospital, highest first."""
    if cases_df is None or cases_df.empty:
        return pd.DataFrame(columns=["hospital_name", "cases"])
    return (
        cases_df.groupby("hospital_name").size()
        .reset_index(name="cases")
        .sort_values("cases", ascending=False)
        .reset_index(drop=True)
    )


def age_distribution(cases_df):
    """Cases per age band, always in the configured band order."""
    if cases_df is None or cases_df.empty:
        return pd.DataFrame({"age_band": AGE_BAND_LABELS,
                             "cases": [0] * len(AGE_BAND_LABELS)})
    banded = add_age_band(cases_df)
    counts = banded["age_band"].value_counts()
    return pd.DataFrame({
        "age_band": AGE_BAND_LABELS,
        "cases": [int(counts.get(label, 0)) for label in AGE_BAND_LABELS],
    })


def severity_distribution(cases_df):
    """Cases per severity level, in Mild → Severe order."""
    if cases_df is None or cases_df.empty:
        return pd.DataFrame({"severity": SEVERITY_LEVELS,
                             "cases": [0] * len(SEVERITY_LEVELS)})
    counts = cases_df["severity"].value_counts()
    return pd.DataFrame({
        "severity": SEVERITY_LEVELS,
        "cases": [int(counts.get(level, 0)) for level in SEVERITY_LEVELS],
    })


def gender_distribution(cases_df):
    """Cases per gender."""
    if cases_df is None or cases_df.empty:
        return pd.DataFrame({"gender": GENDERS, "cases": [0] * len(GENDERS)})
    counts = cases_df["gender"].value_counts()
    labels = list(dict.fromkeys(GENDERS + counts.index.tolist()))
    return pd.DataFrame({
        "gender": labels,
        "cases": [int(counts.get(label, 0)) for label in labels],
    })


# --------------------------------------------------------------------------
# Time series & trends
# --------------------------------------------------------------------------
def daily_case_counts(cases_df, condition=None, days=None):
    """Daily case counts, with missing days filled as zero for a clean chart."""
    empty = pd.DataFrame(columns=["case_date", "cases"])
    if cases_df is None or cases_df.empty:
        return empty

    df = cases_df.copy()
    if condition:
        df = df[df["condition"] == condition]
    if df.empty:
        return empty

    df["case_date"] = pd.to_datetime(df["case_date"], errors="coerce")
    df = df.dropna(subset=["case_date"])
    if df.empty:
        return empty

    if days:
        cutoff = df["case_date"].max() - pd.Timedelta(days=days - 1)
        df = df[df["case_date"] >= cutoff]

    series = df.groupby(df["case_date"].dt.date).size()
    if series.empty:
        return empty

    full_index = pd.date_range(min(series.index), max(series.index), freq="D")
    series = series.reindex(full_index.date, fill_value=0)
    return pd.DataFrame({"case_date": pd.to_datetime(list(series.index)),
                         "cases": series.values.astype(int)})


def condition_trend_table(cases_df, window_days=TREND_WINDOW_DAYS,
                          min_cases=MIN_CASES_FOR_TREND):
    """
    Compare the most recent `window_days` against the previous `window_days`
    for every condition and compute a real percentage change.

    Returns a DataFrame with:
        condition, recent_cases, previous_cases, change_pct, direction, enough_data
    `change_pct` is None when there is not enough history to judge.
    """
    columns = ["condition", "recent_cases", "previous_cases", "change_pct",
               "direction", "enough_data"]
    if cases_df is None or cases_df.empty:
        return pd.DataFrame(columns=columns)

    df = cases_df.copy()
    df["case_date"] = pd.to_datetime(df["case_date"], errors="coerce")
    df = df.dropna(subset=["case_date"])
    if df.empty:
        return pd.DataFrame(columns=columns)

    today = pd.Timestamp(datetime.now().date())
    recent_start = today - pd.Timedelta(days=window_days - 1)
    previous_start = recent_start - pd.Timedelta(days=window_days)

    recent = df[df["case_date"] >= recent_start]
    previous = df[(df["case_date"] >= previous_start) & (df["case_date"] < recent_start)]

    # Was there any data at all in the earlier window? If the database simply
    # does not go back that far we must say so rather than invent a trend.
    history_available = (
        not df.empty and df["case_date"].min() <= previous_start + pd.Timedelta(days=2)
    )

    recent_counts = recent["condition"].value_counts()
    previous_counts = previous["condition"].value_counts()

    rows = []
    for condition in sorted(set(recent_counts.index) | set(previous_counts.index)):
        r = int(recent_counts.get(condition, 0))
        p = int(previous_counts.get(condition, 0))

        enough = history_available and (r + p) >= min_cases and p > 0
        if enough:
            change = (r - p) / p * 100.0
            if change >= 10:
                direction = "rising"
            elif change <= -10:
                direction = "falling"
            else:
                direction = "stable"
        else:
            change = None
            direction = "unknown"

        rows.append({
            "condition": condition,
            "recent_cases": r,
            "previous_cases": p,
            "change_pct": change,
            "direction": direction,
            "enough_data": enough,
        })

    out = pd.DataFrame(rows, columns=columns)
    if out.empty:
        return out
    return out.sort_values(
        ["enough_data", "change_pct", "recent_cases"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)


def rising_conditions(cases_df, window_days=TREND_WINDOW_DAYS, top_n=3):
    """The conditions with the largest genuine increase, best first."""
    table = condition_trend_table(cases_df, window_days=window_days)
    if table.empty:
        return table
    rising = table[(table["direction"] == "rising") & table["enough_data"]]
    return rising.head(top_n).reset_index(drop=True)


def format_trend_label(row):
    """Human-readable trend text for a row of `condition_trend_table`."""
    if not row.get("enough_data") or row.get("change_pct") is None:
        return "Insufficient historical data to determine a trend."
    change = row["change_pct"]
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.0f}% compared with previous period"


# --------------------------------------------------------------------------
# Hospital crowd
# --------------------------------------------------------------------------
def crowd_status(patients_waiting, thresholds=None):
    """Map a queue size to Low / Moderate / High using configurable thresholds."""
    if patients_waiting is None or (isinstance(patients_waiting, float)
                                    and np.isnan(patients_waiting)):
        return "Unknown"
    thresholds = thresholds or CROWD_THRESHOLDS
    value = int(patients_waiting)
    if value <= thresholds["low_max"]:
        return "Low"
    if value <= thresholds["moderate_max"]:
        return "Moderate"
    return "High"


def annotate_crowd_status(latest_df, thresholds=None):
    """Add a `status` column to the latest-queue frame."""
    if latest_df is None or latest_df.empty:
        return latest_df
    out = latest_df.copy()
    out["status"] = out["patients_waiting"].apply(
        lambda v: crowd_status(v, thresholds)
    )
    return out


def describe_time_ago(timestamp):
    """'5 minutes ago' style string for the 'last updated' line."""
    if timestamp is None or pd.isna(timestamp):
        return "No reported data yet"
    if not isinstance(timestamp, datetime):
        timestamp = pd.to_datetime(timestamp, errors="coerce")
        if pd.isna(timestamp):
            return "No reported data yet"
        timestamp = timestamp.to_pydatetime()

    delta = datetime.now() - timestamp
    seconds = delta.total_seconds()
    if seconds < 0:
        return timestamp.strftime("%d %b, %I:%M %p")
    if seconds < 120:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    if seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    days = int(seconds // 86400)
    return f"{days} day{'s' if days > 1 else ''} ago"


def queue_profile(queue_df):
    """
    Summary statistics for one hospital's queue history:
    average crowd, busiest hour, quietest hour, peak day.
    """
    profile = {
        "average_patients": None,
        "average_wait": None,
        "busiest_hour": None,
        "quietest_hour": None,
        "busiest_day": None,
        "records": 0,
    }
    if queue_df is None or queue_df.empty:
        return profile

    df = queue_df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
    df = df.dropna(subset=["recorded_at"])
    if df.empty:
        return profile

    df["hour"] = df["recorded_at"].dt.hour
    df["day_name"] = df["recorded_at"].dt.day_name()

    hourly = df.groupby("hour")["patients_waiting"].mean()
    daily = df.groupby("day_name")["patients_waiting"].mean()

    profile.update({
        "average_patients": float(df["patients_waiting"].mean()),
        "average_wait": float(df["estimated_waiting_minutes"].mean()),
        "busiest_hour": int(hourly.idxmax()) if not hourly.empty else None,
        "quietest_hour": int(hourly.idxmin()) if not hourly.empty else None,
        "busiest_day": str(daily.idxmax()) if not daily.empty else None,
        "records": int(len(df)),
    })
    return profile


def hourly_average_crowd(queue_df):
    """Average patients waiting by hour of day — used for the pattern chart."""
    if queue_df is None or queue_df.empty:
        return pd.DataFrame(columns=["hour", "avg_patients"])
    df = queue_df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
    df = df.dropna(subset=["recorded_at"])
    if df.empty:
        return pd.DataFrame(columns=["hour", "avg_patients"])
    out = (
        df.assign(hour=df["recorded_at"].dt.hour)
        .groupby("hour")["patients_waiting"].mean()
        .reset_index(name="avg_patients")
        .sort_values("hour")
    )
    return out


def format_hour(hour):
    """24h int -> '11:00 AM'."""
    if hour is None:
        return "Not available"
    return datetime.strptime(str(int(hour)), "%H").strftime("%I:%M %p").lstrip("0")


def location_crowd_summary(latest_df):
    """One-line summary used on the homepage ('2 of 3 hospitals busy')."""
    if latest_df is None or latest_df.empty:
        return {"total_waiting": 0, "reporting": 0, "busy": 0, "hospitals": 0}
    annotated = annotate_crowd_status(latest_df)
    reporting = annotated["patients_waiting"].notna().sum()
    return {
        "total_waiting": int(annotated["patients_waiting"].fillna(0).sum()),
        "reporting": int(reporting),
        "busy": int((annotated["status"] == "High").sum()),
        "hospitals": int(len(annotated)),
    }
