# Connected Healthcare — Dataset Documentation Report

## 1. Executive Data Quality Statement

- **Dataset Nature:** Simulated / Synthetic Demonstration Data generated for academic evaluation and hospital operations decision-support demonstration.
- **Live Electronic Health Record (EHR) Status:** No live external hospital API or Patient Health Information (PHI) feed is currently connected.
- **Generator Script:** `data/data_generator.py` (reproducible with `random.seed(42)`).
- **Audit Verification Date:** October 24, 2026.
- **Database Engine:** SQLite 3 (`healthcare.db`, 151,552 bytes).

---

## 2. Database Inventory & Table Overview

| Table Name | Total Records | Earliest Timestamp / Date | Latest Timestamp / Date | Primary Key | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`hospitals`** | 3 | N/A | N/A | `id` | Registered healthcare facility metadata |
| **`hospital_crowd`** | 2,161 | 2026-08-01 08:00:00 | 2026-10-01 10:46:05 | `id` | Hourly operational hospital observations |
| **`health_cases`** | 480 | 2026-08-01 | 2026-09-29 | `id` | Daily public health disease case counts |
| **`health_information`**| 4 | N/A | N/A | `id` | Symptom, prevention, and medical guidance |

---

## 3. Schema Definitions & Table Specifications

### A. Table: `hospitals`
Contains registered hospital facilities and their administrative districts.

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique hospital identifier |
| `name` | TEXT | NOT NULL, UNIQUE | Official name of facility |
| `location` | TEXT | NOT NULL | District / geographic jurisdiction |

#### Master Records:
1. `Apollo Hospital` — Chittoor (721 crowd records)
2. `Government General Hospital` — Chittoor (720 crowd records)
3. `Sri Venkateswara Hospital` — Tirupati (720 crowd records)

---

### B. Table: `hospital_crowd`
Contains operational demand records logged hourly during clinical operating hours (08:00 to 19:00, 12 hours/day) across 60 days, plus 1 manually entered user observation.

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique observation record ID |
| `hospital_id` | INTEGER | NOT NULL, FK(`hospitals.id`) | Foreign key linking to hospital |
| `people_waiting` | INTEGER | NOT NULL | Number of patients in waiting room |
| `waiting_minutes` | INTEGER | NOT NULL | Estimated wait time in minutes |
| `new_patients` | INTEGER | DEFAULT 0 | New patient arrivals in preceding hour |
| `discharged_patients` | INTEGER | DEFAULT 0 | Patients treated and discharged in hour |
| `emergency_cases` | INTEGER | DEFAULT 0 | Acute cases admitted to emergency room |
| `holiday` | INTEGER | DEFAULT 0 | Binary flag (1 = Public Holiday, 0 = Normal) |
| `special_event` | TEXT | DEFAULT 'None' | Operational event descriptor |
| `recorded_at` | TEXT | NOT NULL | ISO timestamp (`YYYY-MM-DD HH:MM:SS`) |

#### Verified Distribution Statistics:
- **Total Records:** 2,161
- **Missing Values:** 0 nulls across all columns (100% complete)
- **Duplicate Records:** 0 duplicate `(hospital_id, recorded_at)` pairs
- **Negative Values:** 0 negative values detected
- **People Waiting:** Minimum 10, Mean 37.54, Median 37.0, Maximum 89.0
- **Waiting Minutes:** Minimum 13, Mean 48.13, Median 47.0, Maximum 96.0
- **New Patients / Hour:** Minimum 1, Mean 9.38, Maximum 30.0
- **Discharged Patients / Hour:** Minimum 1, Mean 5.95, Maximum 14.0
- **Emergency Cases / Hour:** Minimum 0, Mean 0.14, Maximum 7.0
- **Holiday Observations:** 144 records (6.7% of total)
- **Special Event Distribution:**
  - `None`: 2,004 records (92.7%)
  - `Emergency`: 69 records (3.2%)
  - `Disease Outbreak`: 50 records (2.3%)
  - `Local Event`: 38 records (1.8%)

---

### C. Table: `health_cases`
Daily public health disease surveillance records tracking 4 conditions across 2 locations for 60 consecutive days ($60 \times 2 \times 4 = 480$ records).

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique record ID |
| `condition` | TEXT | NOT NULL | Name of tracked health condition |
| `location` | TEXT | NOT NULL | District where reports occurred |
| `cases` | INTEGER | NOT NULL | Number of diagnosed daily cases |
| `date` | TEXT | NOT NULL | Date string (`YYYY-MM-DD`) |

#### Condition Case Summary:
| Condition | Records | Min Daily | Mean Daily | Max Daily | Cumulative Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Fever** | 120 | 35 | 49.2 | 63 | 5,904 |
| **Respiratory Infection** | 120 | 21 | 42.2 | 67 | 5,061 |
| **Dengue** | 120 | 10 | 25.9 | 62 | 3,112 |
| **Diabetes** | 120 | 4 | 16.4 | 39 | 1,962 |
| **Total** | **480** | — | — | — | **16,039** |

---

### D. Table: `health_information`
Provides educational medical information for patient and public guidance.

| Condition | Symptoms | Prevention Strategy | Medical Guidance |
| :--- | :--- | :--- | :--- |
| **Fever** | High body temperature, chills, weakness | Stay hydrated, maintain hygiene | Seek help if persistent > 3 days |
| **Respiratory Infection** | Cough, sore throat, breathing difficulty | Hand hygiene, mask wearing | Seek help for severe breathing distress |
| **Dengue** | Fever, headache, body pain, skin rash | Vector control, mosquito protection | Seek attention for severe abdominal pain |
| **Diabetes** | Increased thirst, frequent urination | Healthy diet, active lifestyle | Consult physician for glucose management |

---

## 4. Synthetic Data Generation Mechanics

The operational simulation in `data/data_generator.py` follows an autoregressive stochastic model:

1. **Hospital Capacity Scaling:**
   $$\text{Apollo Factor} = 1.15 \times \text{Base}, \quad \text{GGH Factor} = 1.00 \times \text{Base}, \quad \text{SVH Factor} = 0.85 \times \text{Base}$$

2. **Temporal Demand Curve:**
   - Morning Peak (09:00–11:00): $1.25\times$ arrival multiplier.
   - Evening Peak (17:00–19:00): $1.30\times$ arrival multiplier.
   - Weekend Multiplier: $1.12\times$.
   - Public Holiday Multiplier: $1.18\times$.

3. **Autoregressive Crowd Flow Formulation:**
   $$\text{Crowd}_t = 0.80 \times \text{Crowd}_{t-1} + 0.45 \times (\text{New Patients}_t - \text{Discharges}_t) + 1.3 \times \text{Emergencies}_t + \text{Hidden Demand}_t + \mathcal{N}(0, 4)$$

4. **Waiting Time Dependent Function:**
   $$\text{Waiting Minutes}_t = 20 + 0.75 \times \text{Crowd}_t + 4 \times \text{Emergencies}_t + \mathcal{N}(0, 5)$$

---

## 5. Cleaning, Validation & Quality Assurance

- **Zero Imputation on Target:** In training, rows with unobserved next targets (the final record of each hospital) are omitted rather than imputed to avoid synthetic target distortion.
- **Negative Value Clamping:** Operational counts (crowd, waiting time) are enforced $\ge 0$ at ingestion and inference time.
- **Strict Data Types:** Ingested inputs are validated via `src/data_validation.py` using parameterized SQL to prevent type confusion or SQL injection.

---

## 6. Dynamic Simulation Engine & Real-Time Generator

To enable dynamic viva demonstrations and automated deployment onto fresh machines without an existing database:

1. **Auto-Initialization Fallback:**
   - On application startup, `src/synthetic_generator.py::ensure_database_populated()` verifies database existence and record counts.
   - If tables are empty or missing, it dynamically generates the full 60-day baseline dataset (3 hospitals, 2,160 observations, 480 disease reports, and health guidance).
   - If usable records already exist, it reuses all existing records untouched.

2. **Controlled Next-Hour Simulation (`simulate_next_observation`):**
   - Administrators can advance a hospital's timeline by one simulated operating hour via the `🎲 Simulate Next Hour` button.
   - Computes realistic stochastic arrivals, discharges, emergency cases, and autoregressive crowd memory.
   - Advances time between 08:00 and 19:00 operating hours, rolling over across day boundaries.

3. **Duplicate Prevention on Refresh:**
   - Simulation actions are triggered solely on explicit user button clicks or when the auto-refresh toggle is explicitly checked.
   - The generator checks for existing `(hospital_id, recorded_at)` pairs before inserting.
   - Merely refreshing the browser page or switching tabs never creates duplicate records.
