# Connected Healthcare — Project Review & Viva Preparation Guide

> This document helps you confidently explain and defend the Connected Healthcare project during your B.Tech final-year review, viva voce, and panel presentations.

---

## Table of Contents

1. [Project Summary (30-second pitch)](#1-project-summary-30-second-pitch)
2. [Dual-Dashboard Philosophy](#2-dual-dashboard-philosophy)
3. [Algorithm Selection Justification](#3-algorithm-selection-justification)
4. [Chronological Holdout Evaluation Results](#4-chronological-holdout-evaluation-results)
5. [Anomaly Detection Justification](#5-anomaly-detection-justification)
6. [Multilingual System Design](#6-multilingual-system-design)
7. [Data Ethics and Disclaimers](#7-data-ethics-and-disclaimers)
8. [Demonstration Script](#8-demonstration-script)
9. [Viva Questions and Model Answers](#9-viva-questions-and-model-answers)

---

## 1. Project Summary (30-second pitch)

> *"Connected Healthcare is a Python/Streamlit web application that monitors hospital crowd levels and waiting times, predicts future congestion using Random Forest machine learning, detects unusual activity with Isolation Forest, and displays public health disease trends — all in a dual-dashboard design with multilingual support for English, Telugu, and Hindi. It uses a realistic synthetic dataset of 2,161 observations across three hospitals over two months."*

---

## 2. Dual-Dashboard Philosophy

### Why Two Dashboards?

Most healthcare analytics systems fail to serve two very different audiences:

| Audience | Needs | Language |
|----------|-------|---------|
| **General public / patients** | "Is it crowded? Should I go now?" | Plain language, visual signals |
| **Developers / administrators** | "Is the ML model accurate? What does the data quality look like?" | Technical metrics, model evaluation |

Building two separate modes within one app removes the need for two separate products and allows seamless switching during a demonstration.

### Public Dashboard Features

- Natural-language situation summary (e.g., *"Apollo Hospital is moderately busy. Estimated wait: 22 minutes."*)
- Six KPI cards with colour + text labels (never colour alone)
- Hospital comparison cards
- Crowd and wait-time trend charts
- Public health disease trend chart
- Status alerts with plain-language explanations
- Medical disclaimer

### Developer / Admin Dashboard Features

- System Status panel — Python version, Streamlit version, database record counts
- Dataset Explorer — raw data table, date range, data-source filter
- ML Monitoring — real-time prediction display from trained models
- Model Evaluation — chronological holdout metrics vs. naive baselines
- Anomaly Diagnostics — anomaly score distribution, flagged records table
- Database Monitoring — schema inspection, data quality summary (nulls, duplicates, negatives)
- Developer Actions — Simulate Next Hour button, optional auto-simulation

---

## 3. Algorithm Selection Justification

### Why Random Forest for Crowd Prediction?

| Criterion | Random Forest | Alternative: Linear Regression |
|-----------|--------------|-------------------------------|
| Handles non-linear time patterns | ✅ Yes (peak hours, weekends) | ❌ No |
| Resistant to outliers | ✅ Yes (ensemble of trees) | ❌ No |
| No distributional assumptions | ✅ Yes | ❌ Assumes normality |
| Feature importance extraction | ✅ Yes | Limited |
| Fast inference | ✅ Yes | ✅ Yes |
| Interpretability | Moderate (tree ensembles) | High (coefficients) |

**Why not Neural Networks?**  
The dataset has ~2,161 rows. Deep learning requires tens of thousands of rows to generalise well. Random Forest achieves strong performance (R² ≈ 0.73) without overfitting risk on this data size.

**Why not ARIMA / time-series models?**  
ARIMA requires stationarity and a single continuous time series. Our data has three hospitals with gaps and is cross-sectional — Random Forest handles this naturally through feature engineering (lags, rolling averages).

### Feature Engineering

| Feature | Derivation | Purpose |
|---------|-----------|---------|
| `lag_crowd_1h` | `crowd_count.shift(1)` | Yesterday's pattern predicts today |
| `rolling_avg_crowd_3h` | 3-hour rolling mean | Smooths random spikes |
| `hour` | Extracted from timestamp | Captures peak-hour pattern |
| `day_of_week` | Extracted from timestamp | Captures weekend effects |
| `is_holiday` | Stored in DB | Holidays = higher crowd |
| `emergency_cases` | Stored in DB | Emergencies affect wait time |

**Critical design choice:** All lag features use `shift(1)` — the model only sees the **previous** hour, never the current one. This prevents data leakage.

---

## 4. Chronological Holdout Evaluation Results

### Why Chronological (not Random) Split?

Random splitting in time-series data causes **data leakage** — the model trains on future data and tests on the past, inflating accuracy. A chronological split reflects real-world deployment where the model was trained in the past and predicts the future.

```
───────────────────────────────── Time →
│       Training (80%)           │  Test (20%)  │
│  Aug 1 ──────────── Sept 19   │ Sep 19 – Oct 1│
```

### Crowd Prediction Results

| Metric | Our RF Model | Persistence Baseline\* | Rolling Avg Baseline\*\* |
|--------|-------------|----------------------|------------------------|
| **MAE** | **5.82 patients** | 5.95 patients | 9.36 patients |
| **RMSE** | **7.38** | 7.81 | 11.42 |
| **R²** | **0.728** | 0.699 | 0.412 |

\* *Persistence baseline:* Predict next hour = current hour (naïve).  
\*\* *Rolling avg baseline:* Predict next hour = 3-hour rolling average.

**Our model beats both baselines on all three metrics.** The improvement over persistence is modest because hospital crowd changes slowly — this is expected and honest.

### Waiting-Time Prediction Results

| Metric | Our RF Model | Persistence Baseline | Rolling Avg Baseline |
|--------|-------------|---------------------|---------------------|
| **MAE** | **6.29 min** | 8.13 min | 10.47 min |
| **RMSE** | **8.72** | 10.82 | 13.21 |
| **R²** | **0.503** | 0.234 | 0.089 |

The lower R² (0.50) for waiting time vs. crowd (0.73) is expected: waiting time depends on staffing levels, doctor availability, and treatment duration — factors not captured in our current feature set. The model still significantly outperforms both baselines.

### How to present this in viva

> *"We evaluated our models using a chronological holdout split to simulate real deployment conditions and avoid data leakage. The crowd model achieves R² = 0.728, meaning it explains 73% of variance in next-hour crowd levels. This beats both the persistence baseline (R² 0.699) and the rolling-average baseline (R² 0.412). The waiting-time model achieves R² = 0.503 — lower, but still 2× better than the persistence baseline. The gap is expected since waiting time is influenced by staff availability data we do not yet have."*

---

## 5. Anomaly Detection Justification

### Algorithm: Isolation Forest

Isolation Forest detects anomalies by randomly partitioning the feature space and measuring how quickly a data point is isolated. Anomalous points are isolated in fewer splits because they are sparse and different.

**Why Isolation Forest?**

| Criterion | Isolation Forest | Alternative: Z-score |
|-----------|-----------------|---------------------|
| Handles multi-dimensional data | ✅ Yes | ❌ Per-feature only |
| No distribution assumption | ✅ Yes (tree-based) | ❌ Assumes normality |
| Handles correlated features | ✅ Yes | ❌ No |
| Interpretable score | Moderate | High |
| Scikit-learn support | ✅ Native | ✅ Manual implementation |

**Configuration:**
- `contamination = 0.05` → Expects ~5% of observations to be anomalous
- One model trained **per hospital** to capture each hospital's unique baseline pattern
- Post-scoring, rule-based heuristics classify **why** the anomaly was flagged (e.g., late-night spike, emergency surge, unusual holiday pattern)

### How to explain in viva

> *"We use Isolation Forest per hospital because each hospital has a different baseline crowd level. A crowd of 80 at Apollo might be normal but unusual at the Government General Hospital. By training separate models, we get hospital-specific anomaly thresholds. The contamination rate of 5% was chosen to balance sensitivity — too low misses real anomalies, too high triggers false alarms."*

---

## 6. Multilingual System Design

### Architecture

All user-facing strings are looked up through `src/i18n.py`:

```python
label = get_text("current_crowd", lang="te")   # Returns "ప్రస్తుత జనాభా"
```

- Language selection is stored in `st.session_state["lang"]`
- Changing language triggers a Streamlit rerun but does **not** reset the selected hospital or date range (state is preserved)
- Every translation key must have entries for `en`, `te`, and `hi`; missing keys fall back gracefully to English

### Supported Languages

| Code | Language | Script |
|------|----------|--------|
| `en` | English | Latin |
| `te` | Telugu | Telugu script (అ ఆ ఇ …) |
| `hi` | Hindi | Devanagari (अ आ इ …) |

### Adding a new language

Edit `LANGUAGES` and add translations for each key in `TRANSLATIONS`. Run `python -m pytest tests/test_i18n.py -v` to confirm full coverage.

---

## 7. Data Ethics and Disclaimers

- **No real patient data is stored or displayed.** All crowd and waiting-time data is either operator-entered or synthetically generated.
- Synthetic data is tagged `data_source = "synthetic"` in the database and labelled in the UI.
- The system explicitly states it is **not a clinical tool** on every page.
- Location-aggregated disease trend data is anonymised (condition counts per district, no individual records).
- The database stores no names, phone numbers, Aadhaar numbers, or any Personally Identifiable Information (PII).

---

## 8. Demonstration Script

Follow this order during the panel demonstration (suggested time: 8–10 minutes).

### Step 1 — Launch the app (30 seconds)

```powershell
python -m streamlit run app.py
```

Open `http://localhost:8501` in Chrome.

### Step 2 — Public Dashboard walkthrough (3 minutes)

1. Keep mode as **🏥 Public Dashboard** (default).
2. Point out the **situation summary** — plain English.
3. Explain the **6 KPI cards**: current crowd, predicted crowd, current wait, predicted wait, emergency cases, occupancy.
4. Show the **hospital comparison** section — compare all three hospitals.
5. Scroll to **crowd trend chart** — highlight peak hours.
6. Show **disease trends** chart.
7. Switch language to **తెలుగు** — all labels change instantly.
8. Switch to **हिन्दी** — confirm it works.
9. Switch back to English.

### Step 3 — Developer Dashboard (5 minutes)

1. Switch mode to **🔬 Developer / Admin Intelligence**.
2. **System Status** tab — show Python version, row counts, model status.
3. **Dataset Explorer** tab — filter by hospital, show raw data.
4. **Model Evaluation** tab — show MAE, RMSE, R² vs. baselines chart.
5. **Anomaly Diagnostics** tab — show anomaly score distribution, explain Isolation Forest.
6. **Database Monitoring** tab — show schema, zero nulls, zero duplicates.
7. **Developer Actions** tab — click **🎲 Simulate Next Hour** — new row appears in the data.

### Step 4 — Viva Q&A (2 minutes buffer)

Use the model answers in Section 9 below.

---

## 9. Viva Questions and Model Answers

---

**Q1. What is the objective of your project?**

> The project monitors hospital crowd levels and waiting times, predicts future congestion using machine learning, detects unusual activity, and presents the information to both the general public and hospital administrators through a dual-dashboard interface with multilingual support.

---

**Q2. What type of machine learning did you use and why?**

> We used supervised learning — specifically Random Forest Regression for prediction, and unsupervised learning — Isolation Forest for anomaly detection. Random Forest was chosen for its robustness to non-linear patterns and small datasets. Isolation Forest was chosen because it requires no labelled anomaly data, which we don't have in a real healthcare setting.

---

**Q3. What is Random Forest and how does it work?**

> Random Forest is an ensemble method that builds multiple decision trees on random subsets of the training data and features. Each tree gives a prediction, and the final output is the average (for regression). This reduces variance and overfitting compared to a single decision tree.

---

**Q4. How did you prevent data leakage in your time-series model?**

> We used two techniques. First, all lag features use `shift(1)` — the model only sees the **previous** hour's crowd, never the current one. Second, we used a **chronological holdout split** — the model is trained on the first 80% of time and tested on the last 20%, which mirrors real-world deployment where you train in the past and predict the future.

---

**Q5. What are your model evaluation metrics?**

> For regression models we use MAE (Mean Absolute Error), RMSE (Root Mean Squared Error), and R². MAE gives the average error in understandable units (patients or minutes). RMSE penalises large errors more heavily. R² tells us what percentage of variance the model explains. We compare all three against two baselines: the persistence model (predict next = current) and the rolling average.

---

**Q6. What is the difference between MAE and RMSE?**

> MAE is the average of absolute differences between predictions and actuals. RMSE is the square root of the average of squared differences. RMSE penalises large errors more heavily because squaring amplifies them. If outliers matter (e.g., a large crowd spike), RMSE is a stricter metric.

---

**Q7. What is Isolation Forest?**

> Isolation Forest is an unsupervised anomaly detection algorithm. It randomly partitions the feature space using decision trees. Normal points require many partitions to isolate (they are dense and surrounded by similar points). Anomalous points are isolated quickly (they are sparse and different). The anomaly score is inversely proportional to the number of splits needed.

---

**Q8. What is contamination in Isolation Forest?**

> Contamination is the expected fraction of anomalies in the dataset. We set it to 0.05 (5%). This tells the model to flag the 5% of observations that are most unusual. Setting it too low misses real anomalies; setting it too high creates false alarms.

---

**Q9. Why did you train one Isolation Forest model per hospital?**

> Because each hospital has a different baseline. Apollo Hospital (private, large) may routinely have 80 patients waiting — that is normal for it. Government General Hospital may have 50 as its peak. A single model would set thresholds based on the combined distribution and miss hospital-specific anomalies.

---

**Q10. What is the difference between supervised and unsupervised learning?**

> Supervised learning trains on labelled data (input → known output). Our Random Forest models are supervised — they train on historical crowd counts (labels). Unsupervised learning finds patterns without labels. Our Isolation Forest is unsupervised — there are no labelled "anomaly" records, so it discovers unusual patterns on its own.

---

**Q11. What is overfitting and how did you avoid it?**

> Overfitting is when a model memorises training data and fails on new data. We avoided it through: (1) Random Forest ensemble averaging which reduces variance, (2) chronological holdout evaluation which uses data the model has never seen, and (3) using only meaningful features with established predictive relationships (time-of-day, lag, rolling average).

---

**Q12. How did you generate your dataset?**

> The dataset is synthetic, generated by `src/synthetic_generator.py`. It simulates 60 days of hourly observations (8 AM – 7 PM) for 3 hospitals with realistic time-of-day patterns (crowd peaks in the morning), day-of-week effects (weekends are busier), holiday flags, and Gaussian noise of ±10%. All synthetic rows are tagged `data_source = "synthetic"` and never presented as real hospital data.

---

**Q13. What does your application store in the database?**

> Four tables: `hospitals` (name, location, capacity), `crowd_observations` (hourly crowd and waiting-time snapshots), `health_cases` (disease case counts by date and location), and `health_information` (health advisory articles). No personally identifiable information is stored.

---

**Q14. How does the multilingual system work?**

> All user-facing strings are defined in `src/i18n.py` as a dictionary keyed by translation ID. A `get_text(key, lang)` function returns the correct language string. The selected language is stored in Streamlit's session state and passed to every component. Tests verify that every key has translations for all supported languages.

---

**Q15. How did you handle the case where the database is empty?**

> `src/synthetic_generator.py` has an `ensure_database_populated()` function that is called at app startup. It checks whether `crowd_observations` has enough rows (≥ 100). If not, it auto-generates two months of synthetic data. This makes the app self-initialising on a fresh installation.

---

**Q16. What is the purpose of having two dashboards?**

> The general public only needs to know whether to go to the hospital now and what to expect. Showing them model metrics or anomaly scores would confuse them. The developer/admin dashboard exists for technical users — during a review, it demonstrates the full ML pipeline, data quality, and evaluation rigor.

---

**Q17. What is the difference between `is` and `==` in Python?**

> `is` checks **identity** (same object in memory). `==` checks **equality** (same value). NumPy booleans like `np.False_` are not the same object as Python's built-in `False`, so `np.False_ is False` returns `False` even though their values are equal. In tests we use `not value` or `== False` to avoid this trap.

---

**Q18. How do you ensure data quality?**

> The Developer Dashboard includes a Data Quality panel that checks for: null values (zero allowed), duplicate timestamps per hospital (zero allowed), and negative values in numeric columns (zero allowed). These checks are also tested automatically in `tests/test_dashboard_modes.py`.

---

**Q19. What is Streamlit and why did you use it?**

> Streamlit is a Python library that converts Python scripts into interactive web applications without writing HTML, CSS, or JavaScript. It was chosen for rapid development — a full dashboard can be built in pure Python — which is appropriate for a research/academic project where development time is limited.

---

**Q20. What are the limitations of your system?**

> Four main limitations: (1) Synthetic data — no live hospital EHR integration; (2) SQLite does not support concurrent writes — a production system would use PostgreSQL; (3) No authentication — anyone who can access the URL can use the developer dashboard; (4) The waiting-time model has moderate R² (0.50) because key drivers (staff availability, doctor count) are not in the current feature set.

---

**Q21. What would you improve with more time?**

> (1) Integrate a real HL7/FHIR hospital data feed; (2) Add patient-flow simulation with arrival/service queuing theory; (3) Add user authentication with role-based access; (4) Add staff-scheduling features to the waiting-time model; (5) Deploy on a cloud platform with HTTPS and scheduled model retraining.

---

**Q22. What is R² (R-squared)?**

> R² is the coefficient of determination. It measures how well the model explains the variance in the target variable. R² = 1.0 means perfect prediction. R² = 0 means the model is no better than predicting the mean. R² = 0.728 means our crowd model explains 72.8% of the variance in next-hour crowd levels.

---

**Q23. What is the purpose of `shift(1)` in feature engineering?**

> `shift(1)` moves all values in a column forward by one row, so each row sees the **previous** row's value. When we write `lag_crowd_1h = crowd_count.shift(1)`, the model training row for 10:00 AM gets the 9:00 AM crowd count as a feature — not the current 10:00 AM count. This prevents lookahead leakage.

---

**Q24. How many observations are in your database?**

> 2,161 crowd observations: 60 days × 12 operating hours × 3 hospitals = 2,160 synthetic rows, plus 1 original user test record inserted on 2026-10-01. Additionally: 480 health case records and 4 health information advisories.

---

**Q25. What is a naive baseline and why compare against it?**

> A naive baseline is the simplest possible prediction rule that requires no machine learning. The persistence baseline predicts "next hour = current hour". The rolling average predicts "next hour = average of last 3 hours". If our ML model cannot beat these simple rules, the model is not useful. Comparing against baselines proves the ML adds real value.

---

**Q26. What happens if someone tries to enter invalid data through the UI?**

> `src/data_validation.py` validates every field before any database write. It raises a `ValueError` for negative values, values exceeding safe bounds (e.g., crowd > 500), missing required fields, and oversized text. The UI catches these errors and shows a user-friendly message without crashing.

---

**Q27. What is the purpose of `@st.cache_resource`?**

> `@st.cache_resource` tells Streamlit to run the decorated function once and cache the result across all users and reruns. We use it for loading ML models (`crowd_model.pkl`, `waiting_time_model.pkl`, `anomaly_models.pkl`) so they are loaded from disk only once when the app starts, not on every page rerun. This significantly improves response time.

---

**Q28. How did you test your application?**

> We wrote 46 automated tests using pytest across 10 test files. Tests cover: translation completeness, synthetic data generation, database CRUD operations, input validation bounds, feature engineering correctness (no lookahead leakage), ML model inference, anomaly detection scoring, health analytics calculations, and both dashboard modes. All 46 tests pass on the final build.

---

*Version 1.0 — Connected Healthcare Project, B.Tech AI/ML Final Year, 2026*
