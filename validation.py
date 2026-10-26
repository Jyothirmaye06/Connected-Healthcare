"""
Root wrapper for validation.py for backward compatibility.
"""

from src.data_access import get_all_crowd_data as load_hospital_data
from src.data_validation import check_dataframe_health


def main():
    df = load_hospital_data()
    print("Hospital Data Validation Report:")
    health = check_dataframe_health(df)
    print("Total rows:", health["total_records"])
    print("Duplicate timestamps:", health["duplicate_timestamps"])
    print("Negative values:", health["negative_values"])
    print("Missing values present:", health["has_missing"])


if __name__ == "__main__":
    main()