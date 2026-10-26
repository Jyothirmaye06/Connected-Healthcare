# Connected Healthcare — Final-Year B.Tech Viva & Project Review Guide

A complete guide for project viva voce, evaluator presentations, and technical defense.

---

## 1. Project Identity & Overview

- **Project Title:** Connected Healthcare: Hospital Demand Intelligence & Public Health Surveillance
- **Domain:** Artificial Intelligence, Machine Learning, Healthcare Operations Analytics
- **Primary Objective:** Build a functional decision-support application to monitor hospital crowd levels, predict short-term operational demand using machine learning, detect operational anomalies, and visualize public health disease trends.
- **Safety Boundary:** A healthcare operations decision-support system, **not** an autonomous diagnostic or clinical triage system.

---

## 2. Problem Statement & Motivation

### A. Problem Statement
Hospitals face volatile patient surges due to seasonal disease outbreaks, acute emergency incidents, and operational bottlenecks. Traditional hospital monitoring relies on retrospective reporting, leaving administrators unable to anticipate waiting room congestion before patient wait times escalate. Furthermore, community public health surveillance and hospital operations typically function in isolated silos without cross-signal visibility.

### B. Motivation
By combining predictive machine learning (forecasting future crowd and waiting times), unsupervised anomaly detection (flagging multi-variable operational outliers), and community disease tracking in an integrated dashboard, healthcare administrators can proactively allocate clinical resources, balance patient flow across facilities, and anticipate incoming hospital demand.

---

## 3. Existing System vs. Proposed System

| Dimension | Existing / Traditional Approach | Proposed Connected Healthcare System |
| :--- | :--- | :--- |
| **Operational Tracking** | Manual paper logs or retrospective spreadsheets reviewed after shift completion. | Near real-time operational dashboard with structured metric cards. |
| **Forecasting** | Intuitive guessing or static historical averages with no predictive modelling. | Supervised `RandomForestRegressor` models trained on chronological lags to predict next-observation crowd and wait time. |
| **Outlier Detection** | Static single-variable thresholds that miss multi-variable operational anomalies. | `IsolationForest` detecting multi-dimensional operational anomalies across 7 operational variables. |
| **Alert Explanation** | Unexplained amber/red alarms causing alert fatigue. | Transparent rule-based diagnostic layer stating exact root causes (e.g. "Crowd is +37.7 people above recent average; wait time 96 min"). |
| **Community Context** | Public health disease reports completely disconnected from hospital operations. | Integrated "Health Pulse" module showing disease trends alongside facility pressure. |

---

## 4. Technologies Used & Rationale

1. **Python 3.11:** Industry-standard language for machine learning and scientific computing.
2. **Streamlit:** Allows rapid development of clean, interactive, multi-page data dashboards without requiring heavyweight JavaScript frontends.
3. **scikit-learn:** Provides validated, high-performance implementations of `RandomForestRegressor`, `IsolationForest`, and preprocessing pipelines.
4. **SQLite 3:** Lightweight, zero-configuration relational database with ACID compliance, well-suited for a local decision-support demo.
5. **Plotly:** Interactive charts allowing zooming, hovering, and multi-series comparisons.
6. **pytest:** Automated test framework guaranteeing code reliability and test isolation.

---

## 5. Machine Learning Algorithms & Evaluation

### A. Algorithms
1. **Random Forest Regressors (Supervised Forecasting):**
   - Separate models trained for `next_crowd` and `next_waiting_minutes`.
   - 300 decision trees per forest with `min_samples_leaf=2`.
   - Learns non-linear relationships between arrivals, discharges, emergencies, time of day, and waiting times.
2. **Isolation Forest (Unsupervised Anomaly Detection):**
   - Hospital-specific models with 200 isolation trees and 5% contamination rate.
   - Detects multi-variable outliers based on isolation path length without needing labeled anomaly examples.
3. **Rule-Based Operational Status Engine:**
   - Evaluates transparent demo thresholds (crowd deviation $\ge 10$, wait time $\ge 80$ min, etc.) to assign human-readable status labels (Normal, Unusual Activity, Significant Spike).

### B. Evaluation Results (80/20 Chronological Holdout Set)
- **Crowd Prediction:** Random Forest achieves **5.82 people MAE** and **0.728 $R^2$**, outperforming a moving-average baseline (MAE 9.36, $R^2$ 0.311).
- **Waiting Time Prediction:** Random Forest achieves **6.29 min MAE** and **0.503 $R^2$**, significantly outperforming the naive persistence baseline (MAE 8.13 min, $R^2$ 0.234).

---

## 6. Limitations & Future Roadmap

### Limitations:
1. **Synthetic Data:** The current system uses simulated demonstration data generated via stochastic autoregressive formulas; it is not connected to a live hospital EHR feed.
2. **Operational Hours:** Data covers 08:00 to 19:00 clinic hours; overnight shifts (19:00 to 08:00) are not currently modeled.
3. **Non-Causal Relationship:** The correlation between community disease spikes and hospital crowd is contextual and does not clinically prove causation.

### Future Roadmap:
1. Connect via HL7 / FHIR APIs to genuine hospital Electronic Health Record systems.
2. Incorporate live weather and mobility data (e.g. monsoon rains, traffic congestion) as external predictors.
3. Add role-based authentication and audit logging for enterprise multi-hospital deployments.

---

## 7. Top 25 Viva Voce Questions & Answers

### Q1: What is the main objective of Connected Healthcare?
**Answer:** To provide an operational decision-support tool that forecasts short-term hospital crowd and waiting times, detects unusual operational surges, and presents contextual public health disease surveillance.

### Q2: Why is this system described as "decision support" rather than a "diagnostic system"?
**Answer:** It models operational metrics like patient queues and triage wait times to help administrators manage staffing and facility resources. It does not diagnose medical conditions or recommend clinical treatments for individual patients.

### Q3: Why did you choose Random Forest Regressor over Linear Regression or Deep Learning?
**Answer:** Random Forest effectively captures non-linear operational interactions (such as wait times escalating non-linearly with crowd size), is robust to outlier spikes, requires minimal scaling, and is easily explainable to administrators through feature importance rankings. Deep learning would require substantially larger datasets to avoid overfitting.

### Q4: How is target leakage prevented during model training?
**Answer:** All input features are computed strictly from observations up to time $t$. Lags use `shift(1)` and moving averages use past records only. The prediction target at $t+1$ (`shift(-1)`) is never exposed as an input feature. Preprocessing transformers are fitted exclusively on the chronological training split.

### Q5: Why did you use a chronological split instead of K-Fold cross validation?
**Answer:** Time-series operational data is temporally autocorrelated. A random K-Fold split would cause lookahead leakage (using future records to predict past events). A chronological split (first 80% of dates for training, last 20% for testing) guarantees genuine forward forecasting evaluation.

### Q6: What baseline did you compare your machine learning models against?
**Answer:** We benchmarked against a naive persistence baseline (predicting the current value as the next value: $\hat{y}_{t+1} = y_t$) and a 3-period moving average. Random Forest reduced waiting-time forecast error from 8.13 to 6.29 minutes MAE, proving that the model learns genuine predictive patterns.

### Q7: What is Isolation Forest and how does it detect anomalies?
**Answer:** Isolation Forest is an unsupervised algorithm that isolates anomalies using random partitioning trees. Because operational outliers are few and different, they are isolated in fewer splits (shorter path lengths from the root) compared to normal observations.

### Q8: What does the contamination parameter in Isolation Forest represent?
**Answer:** It is an initial tuning parameter representing the expected proportion of outliers in the dataset (set to 0.05, or 5%). It is a demo calibration parameter, not a medically verified anomaly rate.

### Q9: Why is the rule-based operational status separate from the machine learning model?
**Answer:** Machine learning models output statistical numbers or flags without human context. The rule-based layer translates these signals into clear, actionable explanations (e.g., "Waiting time exceeds 80 minutes" or "Crowd is +37.7 people above recent average") so administrators understand why an alert occurred.

### Q10: What is the difference between absolute change and percentage change?
**Answer:** An absolute change is the numerical difference in physical units (e.g., $+37.7\text{ people}$), whereas percentage change is relative to the baseline ($+79.7\%$). Confusing them could mislead administrators into thinking a surge was 37.7% instead of nearly 80%.

### Q11: What features are most important in predicting future crowd?
**Answer:** Feature importance analysis reveals that `people_waiting` (current crowd, ~72%), `hour` of the day (~5.2%), `rolling_avg_3` (~4.1%), `waiting_minutes` (~3.5%), and `new_patients` (~3.0%) are the top predictors.

### Q12: How does the system handle the cold start or single-observation problem?
**Answer:** If only one historical observation exists, the feature pipeline gracefully imputes missing lags using the current observation's values rather than raising missing-value errors.

### Q13: What database is used, and how is data integrity maintained?
**Answer:** SQLite 3 is used. Parameterized queries (`?` binding) prevent SQL injection, database transactions ensure atomic writes, and `src/data_validation.py` enforces bounds and non-negative constraints.

### Q14: How many records are in the database, and what is the date coverage?
**Answer:** There are 2,161 hospital crowd observations across 3 hospitals (August 1, 2026 to October 1, 2026) and 480 disease case records across 4 conditions (August 1, 2026 to September 29, 2026).

### Q15: Which hospitals and locations are included in the dataset?
**Answer:** Apollo Hospital (Chittoor), Government General Hospital (Chittoor), and Sri Venkateswara Hospital (Tirupati).

### Q16: What four health conditions are tracked in Health Pulse?
**Answer:** Fever, Respiratory Infection, Dengue, and Diabetes.

### Q17: What does the prediction horizon mean in this application?
**Answer:** It represents the expected operational situation at the next scheduled observation interval (~1 hour during 08:00–19:00 operating hours).

### Q18: What is MAE and RMSE, and why use both?
**Answer:** MAE measures the average absolute error in physical units (people or minutes). RMSE squares the errors before averaging, penalizing occasional large forecasting mistakes more severely.

### Q19: Why are hospital-specific anomaly models trained rather than a single unified model?
**Answer:** Different hospitals have different nominal capacities (e.g., Apollo typical crowd is $\sim 42$, while Sri Venkateswara is $\sim 35$). Training facility-specific Isolation Forests prevents natural size differences from being flagged as anomalies.

### Q20: What happens if an authorized user enters an invalid observation (e.g. negative waiting time)?
**Answer:** `src/data_validation.py` intercepts the payload, raises a `ValidationError`, and displays an informative error message in the UI without modifying the database.

### Q21: What design improvements were made to the Streamlit dashboard?
**Answer:** The original 1,160-line single-page app was restructured into a clean 5-page sidebar layout using Plotly interactive charts, distinct KPI cards, restrained medical color palettes, and clear status alert banners.

### Q22: Can this model predict disease outbreaks?
**Answer:** It does not predict future disease etiology. Instead, it monitors ongoing community disease reports and correlates them with hospital crowd pressure to show whether facility surges coincide with community epidemics.

### Q23: How were the models saved and deployed?
**Answer:** Entire scikit-learn Pipelines (including `ColumnTransformer`, `OneHotEncoder`, and `RandomForestRegressor`) were serialized using `joblib` into `models/crowd_model.pkl` and `models/waiting_time_model.pkl`.

### Q24: How was the software verified and tested?
**Answer:** Using `pytest`, 35 unit and integration tests were executed with 100% pass rate, covering database queries, feature calculations, ML inference, anomaly scoring, and data validation against isolated temporary test databases.

### Q25: What is your primary takeaway from this project?
**Answer:** Machine learning in healthcare operations is most effective when paired with domain discipline: preventing lookahead leakage, benchmarking against naive persistence baselines, and pairing statistical models with transparent, rule-based explanations for decision-makers.

### Q26: What happens if the project is deployed on a fresh system where no usable database exists?
**Answer:** The system features an automatic initialization fallback (`src/synthetic_generator.py::ensure_database_populated`). On launch, if `healthcare.db` is missing or empty, it dynamically synthesizes the full 60-day baseline dataset (3 hospitals, 2,160 hourly observations, 480 disease reports, and guidance text). If valid records already exist, it reuses all existing records untouched.

### Q27: How does the dynamic simulation button work during a viva presentation without creating duplicate records on refresh?
**Answer:** The `🎲 Simulate Next Hour` button computes the next chronological operating hour, realistic arrivals, discharges, and emergencies, and commits the observation in a transaction. Simulations only execute on explicit user button clicks; standard browser reloads or tab navigation do not trigger simulation, preventing duplicate timestamps.
