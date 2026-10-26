# Connected Healthcare — Developer Guide

This guide is intended for developers, evaluators, and system administrators who need to understand, extend, or maintain the Connected Healthcare application.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Directory Structure](#2-directory-structure)
3. [Environment Setup](#3-environment-setup)
4. [Configuration (`config.py`)](#4-configuration-configpy)
5. [Module Reference (`src/`)](#5-module-reference-src)
6. [Database Schema](#6-database-schema)
7. [Machine Learning Pipeline](#7-machine-learning-pipeline)
8. [Retraining Models](#8-retraining-models)
9. [Adding a New Language](#9-adding-a-new-language)
10. [Running Tests](#10-running-tests)
11. [Data Simulation](#11-data-simulation)
12. [Deployment](#12-deployment)
13. [Known Limitations](#13-known-limitations)

---

## 1. Project Overview

**Connected Healthcare** is a Python/Streamlit web application that provides:

- Real-time (or near-real-time) hospital crowd and waiting-time monitoring.
- Machine-learning predictions (Random Forest) for crowd and waiting time.
- Anomaly detection (Isolation Forest) with plain-language explanations.
- A dual-dashboard architecture — a layman-friendly **Public Dashboard** and a technical **Developer/Admin Intelligence Dashboard**.
- Multilingual support: English, Telugu (తెలుగు), Hindi (हिन्दी).

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.64 |
| Data | SQLite 3 via `sqlite3` stdlib |
| ML | scikit-learn 1.9 (Random Forest, Isolation Forest) |
| Data processing | Pandas, NumPy |
| Charts | Plotly Express |
| Serialisation | joblib |
| Testing | pytest 9 |
| Runtime | Python 3.11 |

---

## 2. Directory Structure

```
CONNECTED_HEALTHCARE2/
├── app.py                    # Main Streamlit entry point
├── config.py                 # Central path and threshold configuration
├── healthcare.db             # SQLite database (DO NOT DELETE)
├── requirements.txt          # pip dependencies
├── README.md
│
├── src/                      # Backend service modules
│   ├── __init__.py
│   ├── i18n.py               # Multilingual translation system
│   ├── data_access.py        # Thread-safe SQLite queries & writes
│   ├── data_validation.py    # Input bounds and payload validation
│   ├── feature_engineering.py# Lag/rolling features (no lookahead)
│   ├── prediction.py         # RF inference with @st.cache_resource
│   ├── anomaly_detection.py  # IsolationForest + rule-based diagnosis
│   ├── hospital_intelligence.py # Unified intelligence payload
│   ├── health_analytics.py   # Disease surveillance & trend metrics
│   └── synthetic_generator.py# DB auto-init & simulate_next_observation
│
├── models/                   # Trained model artefacts
│   ├── crowd_model.pkl       # RandomForestRegressor pipeline
│   ├── waiting_time_model.pkl# RandomForestRegressor pipeline
│   └── anomaly_models.pkl    # Per-hospital IsolationForest dict
│
├── scripts/
│   └── train_models.py       # Standalone model training script
│
├── docs/                     # Documentation
│   ├── USER_GUIDE.md
│   ├── DEVELOPER_GUIDE.md    # ← this file
│   ├── ALGORITHM_EXPLANATION.md
│   ├── DATASET_DOCUMENTATION.md
│   ├── PROJECT_REVIEW_GUIDE.md
│   └── SYSTEM_ARCHITECTURE.md
│
└── tests/                    # pytest test suite
    ├── test_i18n.py
    ├── test_synthetic_generator.py
    ├── test_data_access.py
    ├── test_data_validation.py
    ├── test_features.py
    ├── test_predictions.py
    ├── test_anomaly_detection.py
    ├── test_health_analytics.py
    ├── test_dashboard.py
    └── test_dashboard_modes.py
```

---

## 3. Environment Setup

```powershell
# Requires Python 3.11
python --version   # Should print 3.11.x

# Install dependencies
python -m pip install -r requirements.txt

# Verify Streamlit is installed
python -m streamlit --version
```

### `requirements.txt`

```
streamlit
pandas
numpy
scikit-learn
joblib
plotly
pytest
```

> **Important:** Always invoke Python as `python` (not `py` or `python3`) and pytest as `python -m pytest`. Multiple Python versions may exist on the same machine; the `python` alias should resolve to 3.11.

---

## 4. Configuration (`config.py`)

All paths and ML thresholds live in [`config.py`](file:///C:/Users/Jyothrimaye/Desktop/CONNECTED_HEALTHCARE2/config.py). Key attributes:

| Variable | Purpose |
|----------|---------|
| `BASE_DIR` | `pathlib.Path` root of the project |
| `DB_PATH` | Absolute path to `healthcare.db` |
| `MODELS_DIR` | Absolute path to `models/` |
| `CROWD_MODEL_PATH` | Path to `crowd_model.pkl` |
| `WAITING_TIME_MODEL_PATH` | Path to `waiting_time_model.pkl` |
| `ANOMALY_MODELS_PATH` | Path to `anomaly_models.pkl` |
| `CROWD_FEATURES` | List of column names used by the crowd RF model |
| `WAIT_FEATURES` | List of column names used by the wait-time RF model |
| `STATUS_THRESHOLDS` | Dict of `{level: crowd_threshold}` |
| `DEMO_HOSPITALS` | List of hospital names expected in the DB |

> Modify only `config.py` when adding thresholds or feature columns — never hard-code paths in `app.py` or `src/` modules.

---

## 5. Module Reference (`src/`)

### `src/i18n.py`

```python
from src.i18n import get_text, LANGUAGES

# Get a translated label
label = get_text("current_crowd", lang="te")

# Available language codes
print(LANGUAGES)   # {"en": "English", "te": "తెలుగు", "hi": "हिन्दी"}

# Keyword interpolation
msg = get_text("wait_time_message", lang="hi", minutes=22)
```

Translation keys are dictionaries in `TRANSLATIONS`. Every key **must** have entries for `en`, `te`, and `hi`.

---

### `src/data_access.py`

All database I/O goes through this module. It opens a fresh connection per call to remain thread-safe in Streamlit's multi-thread environment.

```python
from src.data_access import (
    get_hospitals_df,
    get_hospital_crowd_history,
    get_all_crowd_data,
    insert_crowd_observation,
    get_health_cases_df,
    get_health_information_df,
)

hospitals = get_hospitals_df()   # Returns pd.DataFrame
history = get_hospital_crowd_history("Apollo Hospital", days=30)
insert_crowd_observation(payload_dict)   # Validated dict
```

All writes use transactions with explicit `conn.commit()`. Exceptions roll back automatically.

---

### `src/data_validation.py`

```python
from src.data_validation import validate_observation_payload

payload = {
    "hospital_id": 1,
    "crowd_count": 45,
    "waiting_time": 20,
    "emergency_cases": 3,
    "is_holiday": 0,
    "special_event": "",
}
validate_observation_payload(payload)   # raises ValueError on bad input
```

Bounds:
- `crowd_count`: 0 – 500
- `waiting_time`: 0 – 300 minutes
- `emergency_cases`: 0 – 50
- `is_holiday`: 0 or 1
- `special_event`: max 200 chars, HTML-stripped

---

### `src/feature_engineering.py`

Generates ML features from a time-sorted DataFrame:

```python
from src.feature_engineering import prepare_features, split_chronological

df_feat = prepare_features(history_df)  # Adds lag_1, rolling_3, hour, day_of_week …
X_train, X_test, y_crowd_train, y_crowd_test, y_wait_train, y_wait_test = split_chronological(df_feat)
```

**No lookahead leakage:** `lag_1` uses `shift(1)`, so the model only sees past data.

---

### `src/prediction.py`

```python
from src.prediction import load_models, predict_hospital

crowd_model, wait_model = load_models()   # Cached by @st.cache_resource
result = predict_hospital("Apollo Hospital")
# Returns {"predicted_crowd": 42.3, "predicted_wait": 18.7, "hospital": "Apollo Hospital"}
```

---

### `src/anomaly_detection.py`

```python
from src.anomaly_detection import load_anomaly_models, evaluate_observation_anomaly, generate_status

anomaly_models = load_anomaly_models()
score = evaluate_observation_anomaly(anomaly_models, "Apollo Hospital", observation_row)
status = generate_status(score, crowd=45, waiting_time=20, emergency=3)
```

`generate_status` returns a dict with:
- `level`: `"normal"` | `"moderate"` | `"high"` | `"critical"` | `"unusual"`
- `label`: Localised display string
- `reason`: Plain-language explanation

---

### `src/synthetic_generator.py`

```python
from src.synthetic_generator import ensure_database_populated, simulate_next_observation

ensure_database_populated()  # Auto-inits DB if empty; safe to call on every boot
new_row = simulate_next_observation("Apollo Hospital")  # Returns the inserted dict
```

`simulate_next_observation` uses time-of-day patterns, day-of-week weights, and ±10% Gaussian noise. It refuses to insert a duplicate if a record for the same hospital and hour already exists.

---

## 6. Database Schema

Database file: `healthcare.db` (SQLite 3)

### `hospitals` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT | Hospital name |
| `location` | TEXT | City/district |
| `capacity` | INTEGER | Total bed/waiting capacity |

### `crowd_observations` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `hospital_id` | INTEGER FK | References `hospitals.id` |
| `timestamp` | TEXT | ISO 8601 datetime |
| `crowd_count` | INTEGER | Patients currently waiting |
| `waiting_time` | INTEGER | Estimated wait (minutes) |
| `emergency_cases` | INTEGER | High-priority cases |
| `is_holiday` | INTEGER | 0 or 1 |
| `special_event` | TEXT | Free text tag |
| `data_source` | TEXT | `"real"` or `"synthetic"` |

### `health_cases` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `hospital_id` | INTEGER FK | References `hospitals.id` |
| `report_date` | TEXT | Date of report (YYYY-MM-DD) |
| `condition` | TEXT | Disease / condition name |
| `case_count` | INTEGER | Number of reported cases |
| `location` | TEXT | Reporting area |

### `health_information` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `title` | TEXT | Article/advisory title |
| `content` | TEXT | Full text |
| `category` | TEXT | Topic category |
| `published_date` | TEXT | Publication date |

---

## 7. Machine Learning Pipeline

### Crowd Prediction Model

- **Algorithm:** `RandomForestRegressor` (scikit-learn Pipeline with `StandardScaler`)
- **Features:** `hour`, `day_of_week`, `is_holiday`, `lag_crowd_1h`, `rolling_avg_crowd_3h`, `emergency_cases`
- **Target:** `crowd_count` for the **next** hour
- **Holdout evaluation (chronological, last 20%):**
  - MAE ≈ 5.82 patients
  - RMSE ≈ 7.38
  - R² ≈ 0.728

### Waiting-Time Model

- **Algorithm:** `RandomForestRegressor`
- **Features:** Same as above plus `crowd_count`
- **Target:** `waiting_time` for the **next** hour
- **Holdout evaluation (chronological, last 20%):**
  - MAE ≈ 6.29 minutes
  - RMSE ≈ 8.72
  - R² ≈ 0.503

### Anomaly Detection

- **Algorithm:** Per-hospital `IsolationForest` (contamination = 0.05)
- **Features:** `crowd_count`, `waiting_time`, `emergency_cases`, `hour`, `day_of_week`
- A score < 0 flags an observation as anomalous.
- Post-scoring, rule-based heuristics add a human-readable reason (e.g., "late-night spike", "emergency surge").

---

## 8. Retraining Models

Run the training script whenever new data is available:

```powershell
python scripts/train_models.py
```

This will:
1. Load all `crowd_observations` from `healthcare.db`.
2. Engineer lag and rolling features.
3. Train crowd and waiting-time RF models on the first 80% (chronological).
4. Evaluate on the remaining 20% and print metrics.
5. Train one `IsolationForest` per hospital on all data.
6. Save `.pkl` files to `models/`.

> After retraining, restart the Streamlit app to reload the new models (they are cached per session).

---

## 9. Adding a New Language

1. Open [`src/i18n.py`](file:///C:/Users/Jyothrimaye/Desktop/CONNECTED_HEALTHCARE2/src/i18n.py).
2. Add the new language code and display name to the `LANGUAGES` dict:

```python
LANGUAGES = {
    "en": "English",
    "te": "తెలుగు",
    "hi": "हिन्दी",
    "ta": "தமிழ்",   # ← new
}
```

3. For every key in `TRANSLATIONS`, add a `"ta"` entry:

```python
"current_crowd": {
    "en": "Current Crowd",
    "te": "ప్రస్తుత జనాభా",
    "hi": "वर्तमान भीड़",
    "ta": "தற்போதைய கூட்டம்",  # ← new
},
```

4. Run `python -m pytest tests/test_i18n.py -v` to verify all keys are covered.
5. The language selector in the sidebar will automatically show the new option.

---

## 10. Running Tests

```powershell
# Run all tests
python -m pytest -v tests/

# Run a specific test file
python -m pytest -v tests/test_predictions.py

# Run with output (useful for debugging)
python -m pytest -v -s tests/
```

### Test Coverage Summary

| Test File | Tests | What It Verifies |
|-----------|-------|-----------------|
| `test_i18n.py` | 4 | Language codes, all keys present, interpolation, fallback |
| `test_synthetic_generator.py` | 5 | DB init, data preservation, simulation, selected hospitals, dashboard data refresh |
| `test_data_access.py` | 7 | Queries, inserts, empty database handling, unknown hospital handling |
| `test_data_validation.py` | 9 | Bounds, negative values, missing fields |
| `test_features.py` | 4 | Lag correctness, no lookahead, chronological split |
| `test_predictions.py` | 4 | Model loading, inference shape, empty input error |
| `test_anomaly_detection.py` | 6 | IsolationForest loading, scoring, status rules |
| `test_health_analytics.py` | 3 | Trend pivoting, community insights |
| `test_dashboard.py` | 3 | Config paths, thresholds, hospital comparison |
| `test_dashboard_modes.py` | 3 | Public summary, developer telemetry, data quality |
| `test_simulation_schedule.py` | 5 | Scheduled tick timing, duplicate-tick guard, lease ownership and expiry |

**Total: 53 collected tests.** The current project test run completed with 53 passing tests.

---

## 11. Data Simulation

The **Developer Actions & Simulation** tab provides both explicit one-time simulation buttons and a scheduled simulator:

1. Select the hospitals to advance and choose an interval (1, 5, or 15 minutes; default 5).
2. Select **Start simulation**. The first tick occurs after one full interval. Each tick adds one synthetic operating-hour observation for every selected hospital.
3. **Pause simulation** suspends ticks; selecting Start again resumes with a fresh full interval. **Stop simulation** disables scheduled ticks.
4. Each successful tick requests a full Streamlit rerun so current metrics, history charts, predictions, and anomaly results are recalculated from the updated database.

The scheduler uses Streamlit fragments and per-browser-session state. A process-wide expiring lease allows only one browser session to run the simulator in a single Streamlit server process. It creates no background thread or independent worker; it runs only while the application session remains connected and the simulator is explicitly started. Stopping the app/session stops updates after the lease expires. Manual batch simulation remains an explicit one-time action and is disabled while scheduled simulation is running.

The lease is in-memory and coordinates sessions within one server process. Do not run multiple Streamlit worker processes against the same SQLite file expecting cross-process simulator locking.

Generated observations are written to the existing `hospital_crowd` table and do not overwrite historical rows. The current schema has no per-record source/provenance column. The dashboard therefore labels the entire dataset and simulator as synthetic demonstration data; it does not represent real or live hospital feeds.

To inspect the latest stored observations without changing the database:

```sql
SELECT h.name, hc.recorded_at, hc.people_waiting, hc.waiting_minutes
FROM hospital_crowd AS hc
JOIN hospitals AS h ON h.id = hc.hospital_id
ORDER BY hc.recorded_at DESC
LIMIT 10;
```

---

## 12. Deployment

### Local (Development)

```powershell
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`.

### Production (simple)

For a local-network deployment (e.g., hospital intranet):

```powershell
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Users on the same network access it via `http://<machine-ip>:8501`.

> For internet deployment, reverse-proxy through NGINX/Caddy and enable HTTPS. Consult Streamlit's official cloud deployment guide for cloud hosting options.

---

## 13. Known Limitations

| Limitation | Impact | Workaround / Future Fix |
|------------|--------|------------------------|
| SQLite single-writer | Concurrent writes may fail | Use PostgreSQL for multi-user production |
| Models loaded per session | Memory overhead with many users | Deploy a separate inference microservice |
| No user authentication | Anyone can use the Developer dashboard | Add Streamlit authentication or OAuth |
| Synthetic data only | No live hospital EHR feed | Integrate a real HL7/FHIR endpoint |
| English fallback for missing keys | Some UI strings may appear in English | Ensure all new keys are added to all languages |

---

*Version 1.0 — Connected Healthcare Project, B.Tech AI/ML Final Year, 2026*
