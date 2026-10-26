"""
Training, benchmarking, and evaluation pipeline for Connected Healthcare.
Trains RandomForestRegressor for crowd and waiting time prediction,
benchmarks against naive baselines, fits hospital-specific IsolationForest models,
and saves validated model artifacts.
"""

import sys
import shutil
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import joblib
from typing import List

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, IsolationForest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    DB_PATH,
    MODELS_DIR,
    MODELS_BACKUP_DIR,
    CROWD_MODEL_PATH,
    WAITING_MODEL_PATH,
    ANOMALY_MODELS_PATH,
    FEATURE_COLUMNS,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    ANOMALY_FEATURE_COLUMNS,
    ISOLATION_FOREST_PARAMS,
)
from src.feature_engineering import prepare_features, split_chronological


def load_raw_crowd_data() -> pd.DataFrame:
    """Loads raw crowd observations joined with hospital metadata."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            hc.id,
            h.name AS hospital,
            h.location,
            hc.people_waiting,
            hc.waiting_minutes,
            hc.new_patients,
            hc.discharged_patients,
            hc.emergency_cases,
            hc.holiday,
            hc.special_event,
            hc.recorded_at
        FROM hospital_crowd hc
        JOIN hospitals h ON hc.hospital_id = h.id
        ORDER BY h.name, hc.recorded_at
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def build_preprocessor() -> ColumnTransformer:
    """Builds preprocessor with imputation and one-hot encoding."""
    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median"))
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    preprocessor = ColumnTransformer([
        ("num", num_pipe, NUMERICAL_FEATURES),
        ("cat", cat_pipe, CATEGORICAL_FEATURES),
    ])
    return preprocessor


def evaluate_predictions(y_true, y_pred):
    """Computes MAE, RMSE, and R2."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return mae, rmse, r2


def backup_existing_models():
    """Preserves current models in models/backup/ before overwriting."""
    MODELS_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for model_path in [CROWD_MODEL_PATH, WAITING_MODEL_PATH, ANOMALY_MODELS_PATH]:
        if model_path.exists():
            backup_target = MODELS_BACKUP_DIR / model_path.name
            shutil.copy2(model_path, backup_target)
            print(f"  [Backup] Preserved: {model_path.name} -> {backup_target}")


def get_feature_names(preprocessor: ColumnTransformer) -> List:
    """Extracts transformed feature names from ColumnTransformer."""
    feature_names = []
    # Numerical
    feature_names.extend(NUMERICAL_FEATURES)
    # Categorical
    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES)
    feature_names.extend(list(cat_names))
    return feature_names


def main():
    print("=" * 75)
    print("CONNECTED HEALTHCARE — MODEL TRAINING & BENCHMARKING PIPELINE")
    print("=" * 75)

    # 1. Load Data
    print("\n1. Loading observations from database...")
    raw_df = load_raw_crowd_data()
    print(f"   Loaded {len(raw_df)} total observations.")

    # 2. Feature Engineering & Target Construction
    print("\n2. Engineering features and defining future targets (t + 1)...")
    feature_df = prepare_features(raw_df, is_training=True)
    print(f"   Observations after target formulation: {len(feature_df)}")

    # 3. Chronological Train / Test Split
    print("\n3. Performing chronological 80/20 train/test split...")
    (
        train_df,
        test_df,
        X_train,
        X_test,
        y_crowd_train,
        y_crowd_test,
        y_wait_train,
        y_wait_test,
    ) = split_chronological(feature_df, test_ratio=0.20)

    train_start, train_end = train_df["recorded_at"].min(), train_df["recorded_at"].max()
    test_start, test_end = test_df["recorded_at"].min(), test_df["recorded_at"].max()
    print(f"   Training Set : {len(train_df)} samples ({train_start} to {train_end})")
    print(f"   Holdout Test : {len(test_df)} samples ({test_start} to {test_end})")

    # =========================================================================
    # CROWD PREDICTION BENCHMARKING
    # =========================================================================
    print("\n" + "=" * 75)
    print("4. CROWD PREDICTION BENCHMARKING (Target: next_crowd in people)")
    print("=" * 75)

    crowd_results = []

    # A. Naive Persistence Baseline (predict current people_waiting as next_crowd)
    y_pred_crowd_naive = X_test["people_waiting"]
    mae, rmse, r2 = evaluate_predictions(y_crowd_test, y_pred_crowd_naive)
    crowd_results.append({
        "Model": "Baseline: Persistence (Current Crowd)",
        "MAE (people)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    # B. Rolling Average Baseline
    y_pred_crowd_roll = X_test["rolling_avg_3"]
    mae, rmse, r2 = evaluate_predictions(y_crowd_test, y_pred_crowd_roll)
    crowd_results.append({
        "Model": "Baseline: Rolling Avg (Past 3-period Mean)",
        "MAE (people)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    # C. Linear Regression
    lr_crowd_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", LinearRegression())
    ])
    lr_crowd_pipe.fit(X_train, y_crowd_train)
    y_pred_lr = lr_crowd_pipe.predict(X_test)
    mae, rmse, r2 = evaluate_predictions(y_crowd_test, y_pred_lr)
    crowd_results.append({
        "Model": "Linear Regression",
        "MAE (people)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    # D. HistGradientBoostingRegressor
    hgb_crowd_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=42))
    ])
    hgb_crowd_pipe.fit(X_train, y_crowd_train)
    y_pred_hgb = hgb_crowd_pipe.predict(X_test)
    mae, rmse, r2 = evaluate_predictions(y_crowd_test, y_pred_hgb)
    crowd_results.append({
        "Model": "HistGradient Boosting Regressor",
        "MAE (people)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    # E. RandomForestRegressor (Primary candidate specified)
    rf_crowd_model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2
    )
    rf_crowd_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", rf_crowd_model)
    ])
    rf_crowd_pipe.fit(X_train, y_crowd_train)
    y_pred_rf_crowd = rf_crowd_pipe.predict(X_test)
    mae, rmse, r2 = evaluate_predictions(y_crowd_test, y_pred_rf_crowd)
    crowd_results.append({
        "Model": "Random Forest Regressor (Selected Primary)",
        "MAE (people)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    df_crowd_res = pd.DataFrame(crowd_results)
    print(df_crowd_res.to_string(index=False))

    # Feature Importance for Random Forest Crowd
    preproc = rf_crowd_pipe.named_steps["preprocessor"]
    rf_estimator = rf_crowd_pipe.named_steps["model"]
    feature_names = get_feature_names(preproc)
    importances = rf_estimator.feature_importances_
    feat_imp = pd.DataFrame({"Feature": feature_names, "Importance": importances}).sort_values("Importance", ascending=False)
    print("\nTop 7 Random Forest Crowd Feature Importances:")
    print(feat_imp.head(7).to_string(index=False))

    # =========================================================================
    # WAITING-TIME PREDICTION BENCHMARKING
    # =========================================================================
    print("\n" + "=" * 75)
    print("5. WAITING-TIME PREDICTION BENCHMARKING (Target: next_waiting_minutes)")
    print("=" * 75)

    wait_results = []

    # A. Naive Persistence Baseline (predict current waiting_minutes as next_waiting_minutes)
    y_pred_wait_naive = X_test["waiting_minutes"]
    mae, rmse, r2 = evaluate_predictions(y_wait_test, y_pred_wait_naive)
    wait_results.append({
        "Model": "Baseline: Persistence (Current Wait)",
        "MAE (mins)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    # B. Linear Regression
    lr_wait_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", LinearRegression())
    ])
    lr_wait_pipe.fit(X_train, y_wait_train)
    y_pred_lr_wait = lr_wait_pipe.predict(X_test)
    mae, rmse, r2 = evaluate_predictions(y_wait_test, y_pred_lr_wait)
    wait_results.append({
        "Model": "Linear Regression",
        "MAE (mins)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    # C. HistGradientBoostingRegressor
    hgb_wait_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=42))
    ])
    hgb_wait_pipe.fit(X_train, y_wait_train)
    y_pred_hgb_wait = hgb_wait_pipe.predict(X_test)
    mae, rmse, r2 = evaluate_predictions(y_wait_test, y_pred_hgb_wait)
    wait_results.append({
        "Model": "HistGradient Boosting Regressor",
        "MAE (mins)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    # D. RandomForestRegressor (Primary candidate specified)
    rf_wait_model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2
    )
    rf_wait_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", rf_wait_model)
    ])
    rf_wait_pipe.fit(X_train, y_wait_train)
    y_pred_rf_wait = rf_wait_pipe.predict(X_test)
    mae, rmse, r2 = evaluate_predictions(y_wait_test, y_pred_rf_wait)
    wait_results.append({
        "Model": "Random Forest Regressor (Selected Primary)",
        "MAE (mins)": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    df_wait_res = pd.DataFrame(wait_results)
    print(df_wait_res.to_string(index=False))

    # =========================================================================
    # ANOMALY DETECTION: ISOLATION FOREST
    # =========================================================================
    print("\n" + "=" * 75)
    print("6. ANOMALY DETECTION MODEL FITTING (Isolation Forest)")
    print("=" * 75)

    anomaly_models = {}
    hospitals = raw_df["hospital"].unique()

    # Create anomaly features
    anomaly_df = prepare_features(raw_df, is_training=False)

    for hosp in hospitals:
        hosp_data = anomaly_df[anomaly_df["hospital"] == hosp].dropna(subset=ANOMALY_FEATURE_COLUMNS)
        iso_forest = IsolationForest(
            n_estimators=ISOLATION_FOREST_PARAMS["n_estimators"],
            contamination=ISOLATION_FOREST_PARAMS["contamination"],
            random_state=ISOLATION_FOREST_PARAMS["random_state"]
        )
        iso_forest.fit(hosp_data[ANOMALY_FEATURE_COLUMNS])
        anomaly_models[hosp] = iso_forest

        preds = iso_forest.predict(hosp_data[ANOMALY_FEATURE_COLUMNS])
        anom_count = (preds == -1).sum()
        print(f"   Hospital '{hosp}': {anom_count} anomalous observations flagged ({anom_count / len(preds) * 100:.1f}%)")

    # =========================================================================
    # BACKUP & PERSISTENCE
    # =========================================================================
    print("\n" + "=" * 75)
    print("7. PERSISTING TESTED MODELS")
    print("=" * 75)

    backup_existing_models()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf_crowd_pipe, CROWD_MODEL_PATH)
    joblib.dump(rf_wait_pipe, WAITING_MODEL_PATH)
    joblib.dump(anomaly_models, ANOMALY_MODELS_PATH)

    print(f"  [Saved] Crowd Model        : {CROWD_MODEL_PATH}")
    print(f"  [Saved] Waiting-Time Model : {WAITING_MODEL_PATH}")
    print(f"  [Saved] Anomaly Models     : {ANOMALY_MODELS_PATH}")

    print("\n" + "=" * 75)
    print("MODEL RETRAINING AND VALIDATION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()
