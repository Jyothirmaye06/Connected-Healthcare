"""
Public Health Analytics module for Connected Healthcare.
Aggregates health-condition reports, computes disease trends,
calculates recent activity metrics (distinguishing absolute difference from percentage change),
and provides contextual decision-support insights.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data_access import get_health_cases_df, get_health_information_df


def get_health_cases_filtered(
    location: Optional[str] = None,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """Returns filtered health cases for analytics."""
    df = get_health_cases_df(location=location, db_path=db_path)
    if df.empty:
        return df

    if start_date is not None:
        df = df[df["date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        df = df[df["date"] <= pd.to_datetime(end_date)]

    return df.sort_values("date").reset_index(drop=True)


def analyze_health_activity(health_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyzes disease activity by comparing the latest recorded date
    against the preceding 7-day moving baseline.

    Crucial Distinction:
    - Absolute Change: latest_cases - recent_average (in patient count)
    - Relative Percentage Change: ((latest_cases - recent_average) / recent_average) * 100
    """
    if health_df.empty:
        return pd.DataFrame()

    results = []
    latest_date = health_df["date"].max()
    conditions = sorted(health_df["condition"].unique())

    for condition in conditions:
        cond_data = health_df[health_df["condition"] == condition].sort_values("date")
        latest_row = cond_data[cond_data["date"] == latest_date]

        if latest_row.empty:
            continue

        latest_cases = int(latest_row["cases"].sum())

        previous_data = cond_data[cond_data["date"] < latest_date]
        if previous_data.empty:
            continue

        recent_dates = previous_data["date"].drop_duplicates().sort_values().tail(7)
        recent_data = previous_data[previous_data["date"].isin(recent_dates)]

        recent_average = float(recent_data["cases"].mean()) if not recent_data.empty else float(latest_cases)
        absolute_difference = latest_cases - recent_average

        if recent_average > 0:
            percentage_change = (absolute_difference / recent_average) * 100.0
        else:
            percentage_change = 0.0

        if percentage_change >= 40.0:
            status = "Significant Increase"
            badge = "🔴"
        elif percentage_change >= 20.0:
            status = "Increased Activity"
            badge = "🟠"
        elif percentage_change <= -20.0:
            status = "Decreased Activity"
            badge = "🔵"
        else:
            status = "Normal"
            badge = "🟢"

        results.append({
            "condition": condition,
            "latest_cases": latest_cases,
            "recent_average": round(recent_average, 1),
            "absolute_difference": round(absolute_difference, 1),
            "percentage_change": round(percentage_change, 1),
            "status": status,
            "badge": badge,
        })

    return pd.DataFrame(results)


def get_health_trend_pivot(health_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivots health cases into a date x condition matrix for Plotly line visualization.
    """
    if health_df.empty:
        return pd.DataFrame()

    df_grouped = health_df.groupby(["date", "condition"])["cases"].sum().reset_index()
    pivot_df = df_grouped.pivot(index="date", columns="condition", values="cases").fillna(0)
    return pivot_df.sort_index()


def generate_community_insight(
    hospital_status: str,
    health_activity_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Synthesizes hospital activity status with community disease surveillance.
    Clearly notes that correlation does not establish medical causation.
    """
    if health_activity_df.empty:
        return {
            "title": "Community Signal",
            "message": "Insufficient community health surveillance data for this selection.",
            "type": "info"
        }

    increased = health_activity_df[
        health_activity_df["status"].isin(["Increased Activity", "Significant Increase"])
    ]["condition"].tolist()

    if hospital_status in ["Unusual Activity", "Significant Spike"]:
        if increased:
            conds_str = ", ".join(increased)
            return {
                "title": "Coinciding Surge Signals",
                "message": (
                    f"Hospital shows {hospital_status} while community surveillance indicates "
                    f"increased activity in {conds_str}. Both operational demand and disease reports "
                    "are elevated. (Decision-Support Notice: This system displays coinciding operational "
                    "trends but does not determine clinical causation)."
                ),
                "type": "warning"
            }
        else:
            return {
                "title": "Isolated Hospital Activity",
                "message": (
                    f"Hospital shows {hospital_status}, but community health-condition reports "
                    "remain within historical baseline levels. The surge may be driven by facility-specific "
                    "factors (e.g. trauma influx, staffing bottlenecks, or local events)."
                ),
                "type": "info"
            }
    else:
        if increased:
            conds_str = ", ".join(increased)
            return {
                "title": "Community Alert with Stable Hospital",
                "message": (
                    f"Community surveillance indicates elevated reports of {conds_str}, but the "
                    "selected hospital operations are currently Normal. Facility capacity appears resilient."
                ),
                "type": "info"
            }
        else:
            return {
                "title": "Stable Baseline Across Hospital & Community",
                "message": "Both hospital operational indicators and community disease metrics are within normal ranges.",
                "type": "success"
            }
