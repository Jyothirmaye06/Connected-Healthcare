"""
Exploratory analytics and reporting utilities for Connected Healthcare.
Provides script-level summaries of hospital demand and community disease patterns.
"""

from src.data_access import get_all_crowd_data, get_health_cases_df, get_hospitals_df
from src.hospital_intelligence import get_all_hospitals_summary
from src.health_analytics import analyze_health_activity, get_health_trend_pivot


def run_full_system_analysis():
    print("=" * 70)
    print("CONNECTED HEALTHCARE — COMPREHENSIVE SYSTEM ANALYSIS")
    print("=" * 70)

    # 1. Hospital Facilities
    hospitals = get_hospitals_df()
    print(f"\n1. Registered Facilities ({len(hospitals)}):")
    for _, h in hospitals.iterrows():
        print(f"   - {h['name']} ({h['location']})")

    # 2. Hospital Operations Summary
    hosp_names = hospitals["name"].tolist()
    summary = get_all_hospitals_summary(hosp_names)
    print("\n2. Latest Hospital Operations & Intelligence:")
    print(summary[["Hospital", "Current Crowd", "Predicted Crowd", "Waiting Time (min)", "Predicted Wait (min)", "Status"]].to_string(index=False))

    # 3. Public Health Activity
    cases_df = get_health_cases_df()
    if not cases_df.empty:
        activity = analyze_health_activity(cases_df)
        print("\n3. Public Health Activity Across Monitored Conditions:")
        print(activity[["condition", "latest_cases", "recent_average", "absolute_difference", "percentage_change", "status"]].to_string(index=False))

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_full_system_analysis()
