"""
models/crowd_model.py
---------------------
Machine-learning layer: predicts how crowded a hospital is likely to be at a
future date/time, using the historical queue records collected in SQLite.

Design notes (useful for the viva):
  * Two targets are modelled: `patients_waiting` and `estimated_waiting_minutes`.
  * Two algorithms are trained and compared: RandomForestRegressor and
    LinearRegression. The better model per target (lowest MAE on a
    chronological hold-out) is used for predictions.
  * The split is chronological, not random — the model is tested on the most
    recent period, which is how it will actually be used.
  * Only features that are genuinely known in advance are used, so there is no
    data leakage: calendar features plus historical averages for that hospital.

This module contains no Streamlit and no SQL.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

from config import MIN_ROWS_FOR_PREDICTION

TARGETS = ["patients_waiting", "estimated_waiting_minutes"]


class InsufficientDataError(Exception):
    """Raised when there is not enough history to train or predict."""


# --------------------------------------------------------------------------
# Feature engineering
# --------------------------------------------------------------------------
def _calendar_features(timestamps):
    """Calendar features that are always known for a future time."""
    ts = pd.to_datetime(pd.Series(timestamps))
    return pd.DataFrame({
        "hour": ts.dt.hour.astype(int).values,
        "day_of_week": ts.dt.dayofweek.astype(int).values,
        "is_weekend": (ts.dt.dayofweek >= 5).astype(int).values,
        "day_of_month": ts.dt.day.astype(int).values,
        # Cyclical encoding so 23:00 and 00:00 are close for the linear model
        "hour_sin": np.sin(2 * np.pi * ts.dt.hour / 24).values,
        "hour_cos": np.cos(2 * np.pi * ts.dt.hour / 24).values,
    })


class CrowdModel:
    """Trains, evaluates and serves the hospital crowd prediction models."""

    def __init__(self):
        self.models = {}           # target -> fitted estimator
        self.chosen = {}           # target -> model name
        self.metrics = {}          # target -> {model name -> metric dict}
        self.feature_names = []
        self.hospital_ids = []
        self._hospital_hour_mean = {}   # (hospital_id, hour) -> mean patients
        self._hospital_mean = {}        # hospital_id -> mean patients
        self._hospital_wait_mean = {}   # hospital_id -> mean waiting minutes
        self.training_rows = 0
        self.trained_until = None
        self.holdout = None        # DataFrame: actual vs predicted (hold-out)

    # ---------------------------------------------------------------- build
    def _build_matrix(self, hospital_ids, timestamps):
        """Assemble the feature matrix for training or prediction."""
        features = _calendar_features(timestamps)
        hospital_ids = pd.Series(list(hospital_ids)).astype(int).reset_index(drop=True)

        # Historical context features (computed from training data only)
        features["hospital_hour_mean"] = [
            self._hospital_hour_mean.get(
                (int(hid), int(hour)),
                self._hospital_mean.get(int(hid), self._global_mean),
            )
            for hid, hour in zip(hospital_ids, features["hour"])
        ]
        features["hospital_mean"] = [
            self._hospital_mean.get(int(hid), self._global_mean)
            for hid in hospital_ids
        ]

        # One-hot encoding of the hospital, with a stable column order
        for hid in self.hospital_ids:
            features[f"hospital_{hid}"] = (hospital_ids == hid).astype(int).values

        return features[self.feature_names] if self.feature_names else features

    # ---------------------------------------------------------------- train
    def train(self, queue_df, test_fraction=0.2):
        """
        Fit and compare models on the supplied queue history.

        queue_df must contain: hospital_id, recorded_at, patients_waiting,
        estimated_waiting_minutes.
        """
        if queue_df is None or len(queue_df) < MIN_ROWS_FOR_PREDICTION:
            raise InsufficientDataError(
                f"At least {MIN_ROWS_FOR_PREDICTION} historical queue records are "
                f"needed to train the model; found {0 if queue_df is None else len(queue_df)}."
            )

        df = queue_df.copy()
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
        df = df.dropna(subset=["recorded_at"]).sort_values("recorded_at")
        df = df.reset_index(drop=True)

        if len(df) < MIN_ROWS_FOR_PREDICTION:
            raise InsufficientDataError("Not enough valid timestamped records to train.")

        self.hospital_ids = sorted(df["hospital_id"].astype(int).unique().tolist())
        self.training_rows = len(df)
        self.trained_until = df["recorded_at"].max()

        # Chronological split: train on the past, test on the most recent slice
        split = max(int(len(df) * (1 - test_fraction)), MIN_ROWS_FOR_PREDICTION // 2)
        split = min(split, len(df) - 1)
        train_df, test_df = df.iloc[:split], df.iloc[split:]

        # Historical aggregates are learned from the TRAINING slice only
        self._global_mean = float(train_df["patients_waiting"].mean())
        self._hospital_mean = (
            train_df.groupby("hospital_id")["patients_waiting"].mean().to_dict()
        )
        self._hospital_wait_mean = (
            train_df.groupby("hospital_id")["estimated_waiting_minutes"].mean().to_dict()
        )
        hour_means = (
            train_df.assign(hour=train_df["recorded_at"].dt.hour)
            .groupby(["hospital_id", "hour"])["patients_waiting"].mean()
        )
        self._hospital_hour_mean = {
            (int(hid), int(hour)): float(value)
            for (hid, hour), value in hour_means.items()
        }

        # Establish the column order once, then reuse it everywhere
        self.feature_names = []
        sample = self._build_matrix(train_df["hospital_id"], train_df["recorded_at"])
        self.feature_names = list(sample.columns)

        X_train = self._build_matrix(train_df["hospital_id"], train_df["recorded_at"])
        X_test = self._build_matrix(test_df["hospital_id"], test_df["recorded_at"])

        holdout = test_df[["hospital_id", "hospital_name", "recorded_at"]].copy() \
            if "hospital_name" in test_df.columns else \
            test_df[["hospital_id", "recorded_at"]].copy()

        for target in TARGETS:
            y_train = train_df[target].values
            y_test = test_df[target].values

            candidates = {
                "Random Forest": RandomForestRegressor(
                    n_estimators=200, max_depth=12, min_samples_leaf=2,
                    random_state=42, n_jobs=-1,
                ),
                "Linear Regression": LinearRegression(),
            }

            scores = {}
            for name, model in candidates.items():
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                scores[name] = {
                    "mae": float(mean_absolute_error(y_test, preds)),
                    "rmse": float(np.sqrt(np.mean((y_test - preds) ** 2))),
                    "r2": float(r2_score(y_test, preds)) if len(set(y_test)) > 1 else float("nan"),
                    "model": model,
                    "preds": preds,
                }

            best_name = min(scores, key=lambda n: scores[n]["mae"])
            self.models[target] = scores[best_name]["model"]
            self.chosen[target] = best_name
            self.metrics[target] = {
                name: {k: v for k, v in score.items() if k in ("mae", "rmse", "r2")}
                for name, score in scores.items()
            }

            holdout[f"actual_{target}"] = y_test
            holdout[f"predicted_{target}"] = np.round(scores[best_name]["preds"], 0)

        # Refit the chosen models on the full history so predictions use
        # everything the database knows.
        X_full = self._build_matrix(df["hospital_id"], df["recorded_at"])
        for target in TARGETS:
            self.models[target].fit(X_full, df[target].values)

        self.holdout = holdout.reset_index(drop=True)
        return self

    # -------------------------------------------------------------- predict
    def predict(self, hospital_id, when):
        """
        Predict the crowd for one hospital at one future (or past) datetime.

        Returns a dict with predicted patients waiting and waiting minutes.
        """
        if not self.models:
            raise InsufficientDataError("The model has not been trained yet.")

        hospital_id = int(hospital_id)
        if hospital_id not in self.hospital_ids:
            raise InsufficientDataError(
                "This hospital has no historical queue records, so no prediction "
                "can be made for it yet."
            )

        X = self._build_matrix([hospital_id], [pd.to_datetime(when)])
        patients = float(self.models["patients_waiting"].predict(X)[0])
        minutes = float(self.models["estimated_waiting_minutes"].predict(X)[0])

        return {
            "hospital_id": hospital_id,
            "predicted_for": pd.to_datetime(when),
            "predicted_patients_waiting": int(max(0, round(patients))),
            "predicted_waiting_minutes": int(max(0, round(minutes))),
            "model_patients": self.chosen["patients_waiting"],
            "model_minutes": self.chosen["estimated_waiting_minutes"],
        }

    def predict_day_curve(self, hospital_id, day, hours):
        """Predict across a list of hours on a given day (for the day-curve chart)."""
        rows = []
        for hour in hours:
            when = pd.Timestamp(day).replace(hour=int(hour), minute=0, second=0)
            try:
                result = self.predict(hospital_id, when)
            except InsufficientDataError:
                continue
            rows.append({
                "hour": int(hour),
                "predicted_patients_waiting": result["predicted_patients_waiting"],
                "predicted_waiting_minutes": result["predicted_waiting_minutes"],
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------ reporting
    def metrics_table(self):
        """Tidy DataFrame comparing both algorithms on both targets."""
        rows = []
        for target, models in self.metrics.items():
            for name, score in models.items():
                rows.append({
                    "Target": ("Patients waiting" if target == "patients_waiting"
                               else "Waiting time (minutes)"),
                    "Model": name,
                    "MAE": round(score["mae"], 2),
                    "RMSE": round(score["rmse"], 2),
                    "R²": round(score["r2"], 3) if score["r2"] == score["r2"] else None,
                    "Selected": "✅" if self.chosen.get(target) == name else "",
                })
        return pd.DataFrame(rows)

    def feature_importance(self, target="patients_waiting", top_n=8):
        """Feature importances for the tree model (empty for linear regression)."""
        model = self.models.get(target)
        if model is None or not hasattr(model, "feature_importances_"):
            return pd.DataFrame(columns=["feature", "importance"])
        out = pd.DataFrame({
            "feature": self.feature_names,
            "importance": model.feature_importances_,
        }).sort_values("importance", ascending=False).head(top_n)
        return out.reset_index(drop=True)


# --------------------------------------------------------------------------
# Convenience wrapper
# --------------------------------------------------------------------------
def train_crowd_model(queue_df):
    """
    Train a CrowdModel. Returns (model, error_message).
    The caller shows `error_message` instead of crashing when data is short.
    """
    try:
        return CrowdModel().train(queue_df), None
    except InsufficientDataError as exc:
        return None, str(exc)
    except Exception as exc:  # pragma: no cover - defensive for the demo
        return None, f"The prediction model could not be trained: {exc}"
