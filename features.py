"""
Root wrapper for features.py for backward compatibility.
"""

from src.data_access import get_all_crowd_data as load_data
from src.feature_engineering import prepare_features


def create_features(df):
    """Generates features and future targets for training."""
    return prepare_features(df, is_training=True)


if __name__ == "__main__":
    df = load_data()
    feat_df = create_features(df)
    print("Features engineered successfully. Rows:", len(feat_df))
    print("Columns:", list(feat_df.columns))