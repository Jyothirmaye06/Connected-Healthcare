import pandas as pd

from features import load_data, create_features


def prepare_dataset():

    print("Loading data...")

    # --------------------------------------------------
    # Load and create features
    # --------------------------------------------------

    df = load_data()

    df = create_features(df)

    # --------------------------------------------------
    # Sort chronologically
    # --------------------------------------------------

    df = df.sort_values("recorded_at")

    # --------------------------------------------------
    # Define target
    # --------------------------------------------------

    target = "next_crowd"

    # --------------------------------------------------
    # Define features
    # --------------------------------------------------

    feature_columns = [
        "hospital",
        "location",
        "hour",
        "day_of_week",
        "is_weekend",
        "people_waiting",
        "previous_crowd",
        "rolling_avg_3",
        "crowd_change",
        "new_patients",
        "discharged_patients",
        "emergency_cases",
        "holiday",
        "special_event",
        "waiting_minutes"
    ]

    X = df[feature_columns]

    y = df[target]

    # --------------------------------------------------
    # Time-based train/test split
    # --------------------------------------------------

    split_index = int(len(df) * 0.80)

    X_train = X.iloc[:split_index]

    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]

    y_test = y.iloc[split_index:]

    # --------------------------------------------------
    # Display information
    # --------------------------------------------------

    print("\nDataset information")
    print("-------------------")

    print("Total records:", len(df))

    print("Training records:", len(X_train))

    print("Testing records:", len(X_test))

    print("\nTraining period:")

    print(
        df["recorded_at"]
        .iloc[:split_index]
        .min()
    )

    print("to")

    print(
        df["recorded_at"]
        .iloc[:split_index]
        .max()
    )

    print("\nTesting period:")

    print(
        df["recorded_at"]
        .iloc[split_index:]
        .min()
    )

    print("to")

    print(
        df["recorded_at"]
        .iloc[split_index:]
        .max()
    )

    print("\nFeatures:")

    for feature in feature_columns:
        print("-", feature)

    print("\nTarget:")
    print("-", target)

    return X_train, X_test, y_train, y_test


if __name__ == "__main__":

    prepare_dataset()