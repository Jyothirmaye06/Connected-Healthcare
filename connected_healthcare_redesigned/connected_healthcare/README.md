# Connected Healthcare

**A Location-Based Healthcare Intelligence and Hospital Crowd Awareness Platform**

Connected Healthcare is an interactive, database-driven Streamlit application that
shows reported health-condition trends for a selected location, displays the
current reported crowd at each hospital, and predicts future hospital crowd using
a machine-learning model trained on historical queue records.

> 🧪 **Demo/Synthetic Data — Not real patient data.** Every record in this project
> is generated for academic demonstration. No names, phone numbers, addresses or
> medical identifiers are used or stored.
>
> ⚠️ This platform provides general health information and reported trends. It does
> **not** diagnose medical conditions and is not a substitute for professional
> medical care.

---

## 1. Quick start

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
streamlit run app.py
```

The database (`healthcare.db`) is created and seeded with synthetic demo data
automatically the first time the app starts. To build it manually:

```bash
python seed_data.py     # wipes and regenerates the demo dataset
```

**Demo admin login** (prototype only): `admin` / `admin123` — configurable in
`config.py`.

---

## 2. Features

The interface deliberately shows only the most useful information first — a
one-line health overview, 2-4 recent conditions, hospital crowd cards, a
one-line trend headline, and condition search. Full charts, tables and ML
internals live on their own pages rather than on the homepage.

| Page | What it does |
|------|--------------|
| 🏠 **Home** (`app.py`) | Location selector, a plain-language health overview, the most-reported conditions, hospital crowd cards, a one-line trend headline, and condition search |
| 🔎 **Health Information** | Per-condition detail: reported cases, one trend chart with a plain-language explanation, a short hospital breakdown, age-group chart, severity counts, plus bullet-point symptoms / prevention / when to seek help |
| 🏥 **Hospitals** | One card per hospital with current reported crowd, estimated waiting time, status and last-updated time; detail view with history, typical daily pattern, busiest/least-busy times, and a short predicted-crowd preview |
| 🔮 **Crowd Prediction** | ML prediction of future patients waiting and waiting time, shown side-by-side with the current reported value. Model comparison, hold-out validation and feature importance are kept for the project demonstration inside a collapsed "Technical details" section, not shown to normal users by default |
| 🔐 **Admin** | Demo-authenticated data entry: crowd updates, reported cases, health information, new hospitals, database status and reseeding |

### Location filtering
Selecting **Chittoor** or **Tirupati** filters *everything*: hospital list, reported
cases, conditions, trends, age-group analysis, hospital distribution, crowd cards
and predictions. Filtering happens in SQL (`WHERE h.location = ?`), not in the UI,
so two cities can never be mixed together. Adding a hospital in a new location from
the Admin page makes that location appear in the selector immediately.

### Current vs predicted — kept strictly separate
- **Current / reported crowd** — the latest value submitted by hospital staff
  through the Admin page, always shown with its timestamp and "x minutes ago".
- **Predicted crowd** — an estimate produced by the ML model for a chosen future
  time, always labelled *"Prediction based on historical data."*

The application never describes reported data as a live hospital feed and never
presents a prediction as current information.

---

## 3. Project structure

```
connected_healthcare/
├── app.py                       # Home page (entry point)
├── config.py                    # Locations, crowd thresholds, age bands, notices
├── database.py                  # Connections + schema (no UI, no analysis)
├── seed_data.py                 # Synthetic demo data generator
├── data_service.py              # Streamlit caching layer (the only cached module)
│
├── pages/
│   ├── 1_🔎_Health_Information.py
│   ├── 2_🏥_Hospitals.py
│   ├── 3_🔮_Crowd_Prediction.py
│   └── 4_🔐_Admin.py
│
├── models/
│   └── crowd_model.py           # scikit-learn training, comparison, prediction
│
├── utils/
│   ├── database_utils.py        # All SQL queries and inserts (pure pandas)
│   ├── analysis_utils.py        # KPIs, trends, distributions, crowd status
│   ├── charts.py                # Plotly chart builders
│   └── ui.py                    # Styling, cards, selectors, notices
│
├── healthcare.db                # Created automatically on first run
├── requirements.txt
└── README.md
```

**Separation of concerns**

- `database.py` / `utils/database_utils.py` — data access only, no Streamlit.
- `utils/analysis_utils.py` — pure pandas analytics, independently testable.
- `models/crowd_model.py` — machine learning only, no SQL and no UI.
- `data_service.py` — the single place where `st.cache_data` / `st.cache_resource`
  are applied.
- `app.py` and `pages/*` — presentation only.

Because the first three layers never import Streamlit, they can be used from a
notebook or a unit test.

---

## 4. Database design

```
hospitals            hospital_id (PK), hospital_name, location
                     UNIQUE(hospital_name, location)

healthcare_cases     case_id (PK), hospital_id (FK → hospitals),
                     condition, age, gender, severity, case_date

hospital_queue       queue_id (PK), hospital_id (FK → hospitals),
                     recorded_at, patients_waiting, estimated_waiting_minutes

health_information   information_id (PK), condition (UNIQUE),
                     symptoms, prevention, when_to_seek_help

crowd_predictions    prediction_id (PK), hospital_id (FK → hospitals),
                     predicted_for, predicted_patients_waiting,
                     predicted_waiting_minutes, created_at
```

Foreign keys are enforced (`PRAGMA foreign_keys = ON`) and indexes exist on
condition, case date, and `(hospital_id, recorded_at)`.

**Queue history is append-only.** Every admin update inserts a *new* timestamped
row instead of overwriting the previous one. That is what makes historical trend
analysis and ML training possible — and it is the key point to make during a viva.

---

## 5. Machine learning

**Task.** Predict `patients_waiting` and `estimated_waiting_minutes` for a
hospital at a chosen future date and time.

**Features** (only information genuinely known in advance, so there is no leakage):
hour of day, cyclical hour encoding (sin/cos), day of week, weekend indicator,
day of month, one-hot encoded hospital, that hospital's historical average crowd
overall and at that hour.

**Models compared.** `RandomForestRegressor` and `LinearRegression` are both
trained; the one with the lower MAE on the hold-out set is selected per target.

**Validation.** The split is **chronological**, not random — the model trains on
older records and is tested on the most recent slice, which is how it is actually
used. The "Predicted vs Actual" chart on the prediction page plots that hold-out
period so the model's quality is visible rather than merely claimed.

Typical demo-data performance: MAE ≈ 3.3 patients, R² ≈ 0.84 for patients waiting.
These numbers describe synthetic data only and are not a claim of operational
accuracy.

If a hospital has fewer than `MIN_ROWS_FOR_PREDICTION` (40) historical records,
the app explains that clearly instead of producing a meaningless prediction.

---

## 6. How trends are calculated

"Recent Health Trends" compares the last **14 days** against the **previous 14
days** for each condition, using real database counts:

```
change % = (recent_cases − previous_cases) / previous_cases × 100
```

A condition is labelled *rising* only above +10%, *falling* only below −10%.
Nothing is randomly labelled as rising. When the database does not go back far
enough, or the counts are too small (< 5 cases), the app states
**"Insufficient historical data to determine a trend."**

All thresholds and windows live in `config.py`.

---

## 7. Data refresh

Cached queries are keyed on a cheap row-count fingerprint of the database
(`data_service.data_version()`) and also carry a 60-second TTL. When an admin
submits an update, the fingerprint changes, the cache key changes, and the public
dashboard shows the new value. A **🔄 Refresh** button on every page clears all
caches manually.

---

## 8. Error handling

The app shows an understandable message instead of crashing when:

- a location has no hospitals or no reported cases,
- a hospital has never reported crowd data,
- there is not enough history for a trend or for the ML model,
- health information is missing for a condition,
- the database cannot be reached or a write is rejected (negative values etc.).

---

## 9. Medical and data-safety position

- The platform reports data and shares general awareness information; it does not
  diagnose, does not interpret personal symptoms and does not recommend medication.
- Wording throughout uses "reported cases", "historical trend" and
  "consider consulting a qualified healthcare professional".
- Predictions are always labelled as estimates from historical data.
- Only anonymous attributes are stored: condition, age, gender, severity, date.
- Authentication is an explicitly labelled demo mechanism, not enterprise security.

---

## 10. Possible extensions

- Compare saved predictions against what actually happened (the
  `crowd_predictions` table is already in place).
- Add more locations and hospitals from the Admin page.
- Hospital-staff accounts with hashed passwords and roles.
- Seasonal features (month, holidays, weather) for the crowd model.

---

## 11. Tech stack

Python • Streamlit • SQLite • Pandas • NumPy • Plotly • scikit-learn
