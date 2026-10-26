import pandas as pd
import os
import joblib 

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from features import load_data, create_features


# --------------------------------------------------
# 1. LOAD AND PREPARE DATA
# --------------------------------------------------

print("Loading data...")

df = load_data()
df = create_features(df)

# Sort chronologically
df = df.sort_values("recorded_at").reset_index(drop=True)


# --------------------------------------------------
# 2. SELECT FEATURES AND TARGET
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

target = "next_crowd"

X = df[feature_columns]
y = df[target]


# --------------------------------------------------
# 3. CHRONOLOGICAL TRAIN / TEST SPLIT
# --------------------------------------------------

split_index = int(len(df) * 0.80)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print("\nDataset")
print("-------------------------")
print("Total records:", len(df))
print("Training records:", len(X_train))
print("Testing records:", len(X_test))

print("\nTraining period:")
print(df["recorded_at"].iloc[:split_index].min())
print("to")
print(df["recorded_at"].iloc[:split_index].max())

print("\nTesting period:")
print(df["recorded_at"].iloc[split_index:].min())
print("to")
print(df["recorded_at"].iloc[split_index:].max())


# --------------------------------------------------
# 4. CATEGORICAL AND NUMERICAL FEATURES
# --------------------------------------------------

categorical_features = [
    "hospital",
    "location",
    "special_event"
]

numerical_features = [
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
    "waiting_minutes"
]


# --------------------------------------------------
# 5. PREPROCESSING
# --------------------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            ),
            categorical_features
        ),
        (
            "numerical",
            "passthrough",
            numerical_features
        )
    ]
)


# --------------------------------------------------
# 6. MODELS
# --------------------------------------------------

models = {

    "Linear Regression": LinearRegression(),

    "Random Forest": RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2
    ),

    "HistGradient Boosting": HistGradientBoostingRegressor(
        max_iter=200,
        learning_rate=0.05,
        max_leaf_nodes=15,
        random_state=42
    )
}


# --------------------------------------------------
# 7. TRAIN AND EVALUATE
# --------------------------------------------------

results = []

print("\n\nMODEL RESULTS")
print("=" * 60)

for model_name, model in models.items():

    print("\nTraining:", model_name)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model)
        ]
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = mean_squared_error(
        y_test,
        predictions
    ) ** 0.5

    r2 = r2_score(
        y_test,
        predictions
    )

    results.append({
        "Model": model_name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    })

    print("MAE :", round(mae, 2))
    print("RMSE:", round(rmse, 2))
    print("R²  :", round(r2, 3))


# --------------------------------------------------
# 8. COMPARISON TABLE
# --------------------------------------------------

results_df = pd.DataFrame(results)

print("\n\nMODEL COMPARISON")
print("=" * 60)

print(
    results_df.to_string(
        index=False
    )
)
# ============================================================
# TRAIN FINAL CROWD MODEL
# ============================================================

print("\n\nTraining final crowd prediction model...")

final_model = HistGradientBoostingRegressor(
    max_iter=200,
    learning_rate=0.05,
    max_leaf_nodes=15,
    random_state=42
)

final_pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            final_model
        )
    ]
)

final_pipeline.fit(
    X_train,
    y_train
)


# ============================================================
# SAVE MODEL
# ============================================================

os.makedirs(
    "models",
    exist_ok=True
)

model_path = os.path.join(
    "models",
    "crowd_model.pkl"
)

joblib.dump(
    final_pipeline,
    model_path
)

print(
    "\nCrowd prediction model saved successfully!"
)

print(
    "Saved to:",
    model_path
)