# Dataset Documentation & Generator Reference

## Overview

The Connected Healthcare dataset is a synthetic demonstration dataset created for college viva presentation, machine learning model evaluation, and hospital operations decision-support demonstration.

**Notice:** This data is simulated/synthetic and does not originate from a verified live Electronic Health Record (EHR) integration or real patient health information (PHI).

## Database: `healthcare.db`

- **Database Engine:** SQLite 3
- **File Size:** ~151.5 KB
- **Preserved Tables:**
  - `hospitals`: 3 healthcare facilities
  - `hospital_crowd`: 2,161 operational observations (August 1, 2026 – October 1, 2026)
  - `health_cases`: 480 disease surveillance records (August 1, 2026 – September 29, 2026)
  - `health_information`: 4 health conditions and symptom guidance

## Data Generation Engine (`data/data_generator.py`)

The dataset was generated using `random.seed(42)` for full scientific reproducibility:

1. **Operating Hours:** 12 hourly observations daily from 08:00 to 19:00 for each hospital.
2. **Diurnal Inflow:** Morning peaks (09:00–11:00) and evening rush hours (17:00–19:00).
3. **Hospital Capacity Factors:**
   - Apollo Hospital: Inflow factor $1.15\times$, initial crowd 42
   - Government General Hospital: Inflow factor $1.00\times$, initial crowd 48
   - Sri Venkateswara Hospital: Inflow factor $0.85\times$, initial crowd 35
4. **Stochastic Events:**
   - Weekend factor ($1.12\times$) and holiday factor ($1.18\times$)
   - Emergency influx (3.5% probability, 2–7 cases)
   - Local events (1.5% probability, +5–12 arrivals)
   - Disease outbreaks (2.0% probability, +5–10 arrivals)
5. **Autoregressive Flow:**
   $$\text{Current Crowd} = \text{Memory Effect} \times \text{Previous Crowd} + \Delta\text{Flow} + \text{Hidden Demand} + \epsilon$$
   $$\text{Waiting Minutes} = 20 + 0.75 \times \text{People Waiting} + 4 \times \text{Emergency Cases} + \mathcal{N}(0, 5)$$

## Schema Details

```sql
CREATE TABLE hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    location TEXT NOT NULL
);

CREATE TABLE hospital_crowd (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER NOT NULL,
    people_waiting INTEGER NOT NULL,
    waiting_minutes INTEGER NOT NULL,
    new_patients INTEGER DEFAULT 0,
    discharged_patients INTEGER DEFAULT 0,
    emergency_cases INTEGER DEFAULT 0,
    holiday INTEGER DEFAULT 0,
    special_event TEXT DEFAULT 'None',
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
);

CREATE TABLE health_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition TEXT NOT NULL,
    location TEXT NOT NULL,
    cases INTEGER NOT NULL,
    date TEXT NOT NULL
);

CREATE TABLE health_information (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition TEXT NOT NULL UNIQUE,
    symptoms TEXT,
    prevention TEXT,
    when_to_seek_help TEXT
);
```
