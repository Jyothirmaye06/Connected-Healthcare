# Connected Healthcare: Public Health Information & Hospital Operations

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-1.64-red.svg)](https://streamlit.io/)
[![ML](https://img.shields.io/badge/scikit--learn-Random%20Forest%20%7C%20Isolation%20Forest-green.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/pytest-project%20suite-blue.svg)](https://pytest.org/)
[![Languages](https://img.shields.io/badge/Languages-English%20%7C%20Telugu%20%7C%20Hindi-orange.svg)]()

A B.Tech AIML demonstration with separate public-health information, hospital operations, staff data-entry, and administrator intelligence pages. Connected Healthcare supports English, తెలుగు, हिन्दी, saved Random Forest forecasts, Isolation Forest anomaly flags, and controlled synthetic-data simulation.

> [!NOTE]
> **Quick Start:** `python -m streamlit run app.py` — then open `http://localhost:8501` in your browser.

---


## 📌 Project Objective & Scope

- **Synthetic Operations Monitoring:** View the most recently stored demonstration observations for crowd, waiting time, arrivals, and emergency cases. This project is not connected to live hospital systems.
- **Machine Learning Forecasting:** Predict future crowd levels and waiting times for the upcoming operational interval (~1 hour) using scikit-learn `RandomForestRegressor`.
- **Operational Anomaly Detection:** Screen multi-dimensional operational metrics using `IsolationForest` to flag abnormal surges.
- **Explainable Status Diagnosis:** Rule-based decision-support assigning clear natural-language reasons for status classifications (Normal 🟢, Unusual Activity 🟡, Significant Spike 🔴).
- **Public Health Information:** Explore synthetic condition-wise demonstration aggregates and project-provided educational text. The database has no verified disease-surveillance feed, hospital-level disease attribution, or age-group data.
- **Hospital Information:** View stored operational observations and separate model forecasts, with stale-data notices.
- **Protected Staff Entry:** Authorized accounts can submit aggregate operational observations restricted to configured hospitals; every insertion is associated with an audit row.
- **Administrator Intelligence:** Monitor the database and loaded model artifacts, inspect operational diagnostics, and run the controlled synthetic simulator.

> [!NOTE]
> **Academic Demonstration & Safety Notice**: This project is not a diagnostic or medical triage system. Existing database observations are synthetic demonstration records; later staff submissions are manual aggregate entries and are not independently verified. The legacy schema does not retain reliable per-observation provenance. No verified live hospital feed is configured.

---

## 🛠️ Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | Core runtime environment |
| **Dashboard UI** | Streamlit | Multipage public site with protected staff and administrator areas |
| **Data Processing** | Pandas, NumPy | Time-series aggregation, rolling averages, lag feature engineering |
| **Database** | SQLite 3 (`healthcare.db`) | Relational operational store with ACID transactions |
| **Machine Learning** | scikit-learn | `RandomForestRegressor` (Regression), `IsolationForest` (Outlier Detection) |
| **Model Persistence** | Joblib | Serialization of preprocessors, pipelines, and estimators |
| **Visualizations** | Plotly | Interactive multi-line time series and grouped bar charts |
| **Testing** | pytest | Automated test suite (53 unit and integration tests) |

---

## 🏗️ Project Architecture

```text
CONNECTED_HEALTHCARE2/
├── app.py                      # Navigation, shared theme, role-aware page registration
├── config.py                   # Central configuration & absolute path resolution
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview & documentation
├── healthcare.db               # Preserved SQLite database
├── data/
│   ├── README.md               # Dataset explanation and schema reference
│   └── data_generator.py       # Preserved synthetic data generation engine
├── models/
│   ├── crowd_model.pkl         # Trained Random Forest crowd model
│   ├── waiting_time_model.pkl  # Trained Random Forest waiting-time model
│   ├── anomaly_models.pkl      # Pre-trained hospital Isolation Forest models
│   └── backup/                 # Recoverable backup of previous models
├── src/
│   ├── __init__.py
│   ├── authentication.py       # PBKDF2 password verification and role/scope checks
│   ├── data_access.py          # SQLite connection manager & queries
│   ├── data_validation.py      # Input validation & schema checks
│   ├── staff_portal.py         # Authorized staff inserts and audit records
│   ├── feature_engineering.py  # Lag features, rolling windows, target formulation
│   ├── prediction.py           # ML inference engine for crowd & wait time
│   ├── anomaly_detection.py    # Isolation Forest & rule-based status diagnosis
│   ├── hospital_intelligence.py# Unified intelligence combining predictions & anomalies
│   ├── health_analytics.py     # Health-condition aggregation and trends
│   ├── site_i18n.py            # Redesigned-site translations
│   └── ui/pages/               # Home, public pages, login, staff portal, admin
├── scripts/
│   ├── generate_password_hash.py # Local interactive PBKDF2 hash helper
│   ├── inspect_dataset.py      # Standalone database quality audit utility
│   └── train_models.py         # Chronological training, baseline benchmarking & evaluation
├── tests/
│   ├── conftest.py             # Pytest fixtures using isolated in-memory test databases
│   ├── test_data_access.py     # Database queries, filtering, error handling
│   ├── test_features.py        # Feature engineering, lag shift verification, no leakage
│   ├── test_predictions.py     # Model inference, non-negativity, edge cases
│   ├── test_anomaly_detection.py # Isolation Forest detection & rule-based status mapping
│   ├── test_data_validation.py # Data entry constraints & validation
│   ├── test_simulation_schedule.py # Scheduled simulation timing and duplicate-tick guard
│   ├── test_health_analytics.py# Absolute difference vs percentage change tests
│   ├── test_dashboard.py       # Configuration & dashboard smoke tests
│   ├── test_authentication_staff_portal.py # Auth, scope, validation, transactional audit
│   └── test_site_pages.py      # Public/protected Streamlit page smoke tests
└── docs/
    ├── DATASET_DOCUMENTATION.md # Comprehensive schema, counts, distributions
    ├── ALGORITHM_EXPLANATION.md # RF Regressor, Isolation Forest, and rule-based status
    ├── SYSTEM_ARCHITECTURE.md   # Architectural design, data flow, pipeline diagram
    └── PROJECT_REVIEW_GUIDE.md  # Viva preparation guide with 25+ viva Q&As
```

---

## ⚡ Quick Start & Execution

### 1. Prerequisites & Installation
Ensure Python 3.11+ is installed. Clone or navigate to the project directory:

```bash
cd C:\Users\Jyothrimaye\Desktop\CONNECTED_HEALTHCARE2
python -m pip install -r requirements.txt
```

### 2. Configure Protected Accounts
See [docs/ACCOUNT_SETUP.md](docs/ACCOUNT_SETUP.md) before configuring any staff or administrator accounts. Public pages work without credentials; protected pages fail closed if no accounts are configured.

### 3. Launch the website

```bash
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Automated Tests
Execute the test suite. Tests that write use isolated temporary databases; dashboard smoke tests may read the configured database:

```bash
python -m pytest -v tests/
```

### 5. Inspect Database Quality
Run the database audit script:

```bash
python scripts/inspect_dataset.py
```

### 6. Retrain and Benchmark Models
Re-run the chronological holdout training pipeline:

```bash
python scripts/train_models.py
```

---

## 📊 Historical Model Evaluation Snapshot

The figures below are a stored snapshot from a prior chronological evaluation run. The dashboard does not recalculate them at startup, and this repository state does not independently establish the exact training/evaluation provenance. Treat these values as illustrative historical results, not as verified current model performance. Re-run the evaluation pipeline on a documented held-out dataset before making performance claims.

### 1. Future Crowd Level Prediction (`next_crowd`)
| Model | MAE (people) | RMSE | $R^2$ | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Baseline: Persistence (Current Crowd)** | 5.95 | 7.56 | 0.715 | Predicts $\hat{y}_{t+1} = \text{crowd}_t$ |
| **Baseline: Moving Average (3 periods)** | 9.36 | 11.74 | 0.311 | Lagged moving average |
| **Linear Regression** | 5.74 | 7.34 | 0.731 | Parametric linear benchmark |
| **Random Forest Regressor (Selected Primary)** | **5.82** | **7.38** | **0.728** | **Non-linear, robust, explainable** |
| **HistGradient Boosting Regressor** | 5.64 | 7.24 | 0.738 | Tree ensemble comparator |

### 2. Future Waiting Time Prediction (`next_waiting_minutes`)
| Model | MAE (mins) | RMSE | $R^2$ | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Baseline: Persistence (Current Wait)** | 8.13 | 10.82 | 0.234 | Predicts $\hat{y}_{t+1} = \text{wait}_t$ |
| **Linear Regression** | 6.22 | 8.65 | 0.511 | Parametric benchmark |
| **Random Forest Regressor (Selected Primary)** | **6.29** | **8.72** | **0.503** | **Reduces MAE by ~1.84 min vs baseline** |
| **HistGradient Boosting Regressor** | 6.45 | 8.86 | 0.487 | Tree ensemble comparator |

---

## 🔒 Safety and Integrity Guarantee

- **Database Preservation:** The original `healthcare.db` database and all 2,161 crowd observations and 480 health case records remain intact.
- **Protected Actions:** No public self-registration exists. Staff scope and role are checked server-side on every submission.
- **Isolated Tests:** Database-writing tests use temporary SQLite databases; some dashboard smoke tests read the configured database.
- **Source Backups:** Timestamped backups of selected changed source, dependency, and documentation files are stored under `.copilot_backups/`. The database and model artifacts were not changed.

## Public-health data limitations

The existing schema stores condition, location, case-row count, and date only. Current case records are synthetic demonstration aggregates; they do not provide verified unique-person counts, age distributions, or hospital-level disease breakdowns. Project-provided symptom and prevention text has no source or review-date metadata and is explicitly identified as unverified educational copy. Official links on the public page are for further reading; the project text is not presented as sourced clinical guidance.

## Authentication and privacy

Passwords are never stored in the source tree or as plaintext. Accounts are provisioned manually in local Streamlit secrets with salted PBKDF2-HMAC-SHA256 hashes and explicit roles/hospital IDs. The staff portal requests aggregate operational counts only. Staff submissions are audited, but existing legacy/simulation rows have no trustworthy per-record origin marker. See [docs/ACCOUNT_SETUP.md](docs/ACCOUNT_SETUP.md).

---

## 📄 License & Attribution

Developed for B.Tech AI/ML Final-Year Project Review.
Connected Healthcare is intended strictly for academic demonstration and decision-support modeling.
