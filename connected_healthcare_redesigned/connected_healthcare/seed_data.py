"""
seed_data.py
------------
Generates the synthetic/demo dataset used by the prototype.

IMPORTANT: every record produced here is artificial. No real patient data,
names, phone numbers, addresses or medical identifiers are used or stored.
Only anonymous attributes (condition, age, gender, severity, date) are kept.
"""

import random
from datetime import datetime, timedelta

import numpy as np

from config import (
    AGE_BANDS,
    GENDERS,
    OPERATING_HOURS,
    SEVERITY_LEVELS,
)
from database import connection_scope, init_db

RANDOM_SEED = 42

# --------------------------------------------------------------------------
# Static reference data
# --------------------------------------------------------------------------
HOSPITALS = [
    ("Apollo Hospital", "Chittoor"),
    ("Government General Hospital", "Chittoor"),
    ("Sri Venkateswara Community Hospital", "Chittoor"),
    ("SVIMS Hospital", "Tirupati"),
    ("Ruia Government Hospital", "Tirupati"),
    ("BIRRD Hospital", "Tirupati"),
]

# Relative size of each hospital — drives both case volume and queue size.
HOSPITAL_SCALE = {
    "Apollo Hospital": 1.0,
    "Government General Hospital": 1.3,
    "Sri Venkateswara Community Hospital": 0.6,
    "SVIMS Hospital": 1.2,
    "Ruia Government Hospital": 1.4,
    "BIRRD Hospital": 0.7,
}

CONDITIONS = [
    "Fever",
    "Dengue",
    "Diabetes",
    "Respiratory Infection",
    "Typhoid",
    "Hypertension",
    "Gastroenteritis",
]

# base_rate       -> average cases per hospital per day at the start of history
# recent_growth   -> multiplier applied over the most recent weeks (creates a
#                    genuine, data-backed rising/falling trend)
# age_weights     -> likelihood per age band (0-17, 18-30, 31-45, 46-60, 61+)
# severity_weights-> likelihood per severity level (Mild, Moderate, Severe)
# surge           -> (window_days, multiplier) extra ramp applied only over the
#                    most recent `window_days`, so the 14-day vs previous-14-day
#                    comparison on the dashboard finds a real, explainable change
CONDITION_PROFILE = {
    "Fever":                 {"base_rate": 2.0, "recent_growth": 1.3,
                              "surge": (30, 1.9),
                              "age_weights": [0.30, 0.25, 0.20, 0.15, 0.10],
                              "severity_weights": [0.65, 0.28, 0.07]},
    "Dengue":                {"base_rate": 0.8, "recent_growth": 1.3,
                              "surge": (30, 2.6),
                              "age_weights": [0.25, 0.30, 0.22, 0.15, 0.08],
                              "severity_weights": [0.35, 0.45, 0.20]},
    "Diabetes":              {"base_rate": 1.4, "recent_growth": 1.05,
                              "age_weights": [0.02, 0.08, 0.25, 0.35, 0.30]},
    "Respiratory Infection": {"base_rate": 1.6, "recent_growth": 1.2,
                              "surge": (30, 1.3),
                              "age_weights": [0.28, 0.18, 0.18, 0.18, 0.18],
                              "severity_weights": [0.50, 0.35, 0.15]},
    "Typhoid":               {"base_rate": 1.0, "recent_growth": 0.9,
                              "surge": (30, 0.5),
                              "age_weights": [0.30, 0.30, 0.22, 0.12, 0.06],
                              "severity_weights": [0.40, 0.45, 0.15]},
    "Hypertension":          {"base_rate": 1.2, "recent_growth": 1.0,
                              "age_weights": [0.01, 0.06, 0.23, 0.38, 0.32],
                              "severity_weights": [0.45, 0.40, 0.15]},
    "Gastroenteritis":       {"base_rate": 1.1, "recent_growth": 0.95,
                              "age_weights": [0.32, 0.26, 0.20, 0.13, 0.09],
                              "severity_weights": [0.60, 0.32, 0.08]},
}

DEFAULT_SEVERITY_WEIGHTS = [0.55, 0.33, 0.12]

# Educational, non-diagnostic health information.
HEALTH_INFORMATION = [
    {
        "condition": "Fever",
        "symptoms": (
            "Raised body temperature; chills or shivering; headache; body ache and "
            "tiredness; sweating; reduced appetite; general weakness."
        ),
        "prevention": (
            "Wash hands regularly with soap; drink safe, clean water; keep living "
            "spaces ventilated; avoid close contact with people who are unwell; "
            "cover the mouth while coughing or sneezing; rest adequately and keep "
            "routine vaccinations up to date."
        ),
        "when_to_seek_help": (
            "Consider consulting a qualified healthcare professional if a fever "
            "lasts more than a few days, is very high, keeps returning, or occurs "
            "along with breathing difficulty, persistent vomiting, confusion, "
            "stiff neck, rash or dehydration. Fever in infants, older adults, "
            "pregnant women and people with existing illnesses deserves earlier "
            "medical attention."
        ),
    },
    {
        "condition": "Dengue",
        "symptoms": (
            "High fever; severe headache; pain behind the eyes; joint and muscle "
            "pain; nausea; skin rash; tiredness that continues after the fever "
            "settles."
        ),
        "prevention": (
            "Remove standing water from coolers, pots, tyres and containers every "
            "week; keep water storage covered; use mosquito nets, screens and "
            "repellents; wear clothing that covers arms and legs during the day; "
            "support community mosquito-control drives."
        ),
        "when_to_seek_help": (
            "Seek appropriate medical care promptly for severe abdominal pain, "
            "repeated vomiting, bleeding from the gums or nose, blood in vomit or "
            "stool, black stools, extreme restlessness, or sudden tiredness after "
            "the fever drops. These are recognised warning signs and need "
            "professional assessment without delay."
        ),
    },
    {
        "condition": "Diabetes",
        "symptoms": (
            "Increased thirst; frequent urination; unexplained weight change; "
            "persistent tiredness; blurred vision; slow-healing wounds; repeated "
            "infections. Some people have no noticeable symptoms early on."
        ),
        "prevention": (
            "Maintain a balanced diet with whole grains, vegetables and pulses; "
            "limit sugary drinks and highly processed food; stay physically active "
            "on most days; maintain a healthy weight; avoid tobacco; attend routine "
            "health check-ups, especially where there is a family history."
        ),
        "when_to_seek_help": (
            "Consider consulting a qualified healthcare professional for testing if "
            "these symptoms are present or if there is a family history. Seek "
            "appropriate emergency medical care for confusion, very rapid breathing, "
            "fruity-smelling breath, severe dehydration, fainting, or symptoms of "
            "very low blood sugar such as sweating with trembling and confusion."
        ),
    },
    {
        "condition": "Respiratory Infection",
        "symptoms": (
            "Cough; sore throat; blocked or runny nose; sneezing; mild fever; "
            "wheezing; chest discomfort; shortness of breath in more serious cases."
        ),
        "prevention": (
            "Wash hands often; wear a mask in crowded indoor settings during "
            "outbreaks; keep rooms ventilated; avoid smoking and second-hand smoke; "
            "reduce exposure to dust and air pollution; keep recommended "
            "vaccinations up to date."
        ),
        "when_to_seek_help": (
            "Seek appropriate medical care for difficulty breathing, chest pain, "
            "bluish lips or face, a cough lasting more than two to three weeks, "
            "coughing up blood, or high fever that does not settle. Infants, older "
            "adults and people with asthma, heart or lung conditions should be "
            "assessed earlier."
        ),
    },
    {
        "condition": "Typhoid",
        "symptoms": (
            "Prolonged fever that rises gradually; stomach pain; weakness; "
            "headache; reduced appetite; constipation or diarrhoea; sometimes a "
            "faint rash."
        ),
        "prevention": (
            "Drink boiled or properly treated water; eat freshly cooked hot food; "
            "wash fruits and vegetables with safe water; wash hands before eating "
            "and after using the toilet; avoid uncovered street food and ice of "
            "unknown source; typhoid vaccination is available — discuss it with a "
            "healthcare professional."
        ),
        "when_to_seek_help": (
            "Consider consulting a qualified healthcare professional for any fever "
            "lasting more than three days. Seek appropriate emergency medical care "
            "for severe abdominal pain, persistent vomiting, blood in stool, or "
            "confusion and drowsiness."
        ),
    },
    {
        "condition": "Hypertension",
        "symptoms": (
            "Often no symptoms at all, which is why it is commonly detected only "
            "during a check-up. Some people report headaches, dizziness or "
            "nosebleeds when readings are very high."
        ),
        "prevention": (
            "Reduce salt intake; eat more fruits, vegetables and whole grains; stay "
            "physically active; maintain a healthy weight; limit alcohol; avoid "
            "tobacco; manage stress and sleep; check blood pressure periodically."
        ),
        "when_to_seek_help": (
            "Consider consulting a qualified healthcare professional for regular "
            "blood-pressure monitoring and advice. Seek appropriate emergency "
            "medical care for chest pain, breathlessness, severe headache with "
            "vision changes, weakness on one side of the body, or difficulty "
            "speaking."
        ),
    },
    {
        "condition": "Gastroenteritis",
        "symptoms": (
            "Loose stools; vomiting; stomach cramps; mild fever; nausea; weakness "
            "and signs of dehydration such as dry mouth and reduced urination."
        ),
        "prevention": (
            "Drink safe water; wash hands with soap before eating and after using "
            "the toilet; eat freshly prepared food; keep cooked and raw food "
            "separate; clean kitchen surfaces and utensils; maintain sanitation "
            "around the home."
        ),
        "when_to_seek_help": (
            "Seek appropriate medical care for signs of dehydration, blood in "
            "stool, continuous vomiting that prevents fluid intake, high fever, or "
            "symptoms lasting more than two to three days. Infants and older adults "
            "should be assessed earlier."
        ),
    },
]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _random_age_for(condition, rng):
    """Pick an age consistent with the condition's age profile."""
    weights = CONDITION_PROFILE[condition]["age_weights"]
    band_index = rng.choice(len(AGE_BANDS), p=np.array(weights) / sum(weights))
    _, low, high = AGE_BANDS[band_index]
    high = min(high, 92)
    return int(rng.integers(low, high + 1))


def _random_severity_for(condition, rng):
    weights = CONDITION_PROFILE[condition].get(
        "severity_weights", DEFAULT_SEVERITY_WEIGHTS
    )
    idx = rng.choice(len(SEVERITY_LEVELS), p=np.array(weights) / sum(weights))
    return SEVERITY_LEVELS[idx]


def _growth_factor(day_offset, total_days, target_growth):
    """
    Smoothly interpolate from 1.0 (oldest day) to `target_growth` (today) so
    that the rising/falling trend is real and reproducible from the data.
    """
    progress = day_offset / max(total_days - 1, 1)
    return 1.0 + (target_growth - 1.0) * progress


def _surge_factor(day_offset, total_days, surge):
    """
    Extra ramp applied only to the final `window` days, used to create a
    realistic recent outbreak (or decline) that the trend analysis can detect.
    """
    if not surge:
        return 1.0
    window, multiplier = surge
    days_from_end = total_days - 1 - day_offset
    if days_from_end >= window:
        return 1.0
    progress = 1.0 - (days_from_end / window)
    return 1.0 + (multiplier - 1.0) * progress


def _crowd_shape(hour, weekday):
    """
    Returns a multiplier describing how busy an OPD typically is at a given
    hour/day. Two peaks: morning (10-12) and evening (17-19).
    """
    morning_peak = np.exp(-((hour - 11) ** 2) / 6.0)
    evening_peak = 0.75 * np.exp(-((hour - 18) ** 2) / 5.0)
    shape = 0.35 + morning_peak + evening_peak
    # Mondays busiest, Sundays quietest
    weekday_factor = [1.25, 1.10, 1.00, 1.00, 1.05, 0.95, 0.70][weekday]
    return shape * weekday_factor


# --------------------------------------------------------------------------
# Seeding routines
# --------------------------------------------------------------------------
def seed_hospitals(conn):
    conn.executemany(
        "INSERT OR IGNORE INTO hospitals (hospital_name, location) VALUES (?, ?);",
        HOSPITALS,
    )
    rows = conn.execute(
        "SELECT hospital_id, hospital_name, location FROM hospitals;"
    ).fetchall()
    return [dict(row) for row in rows]


def seed_health_information(conn):
    conn.executemany(
        """
        INSERT OR IGNORE INTO health_information
            (condition, symptoms, prevention, when_to_seek_help)
        VALUES (:condition, :symptoms, :prevention, :when_to_seek_help);
        """,
        HEALTH_INFORMATION,
    )


def seed_healthcare_cases(conn, hospitals, days=120):
    """Generate anonymous case records across the full history window."""
    rng = np.random.default_rng(RANDOM_SEED)
    today = datetime.now().date()
    records = []

    for hospital in hospitals:
        scale = HOSPITAL_SCALE.get(hospital["hospital_name"], 1.0)
        for day_offset in range(days):
            case_date = today - timedelta(days=days - 1 - day_offset)
            for condition, profile in CONDITION_PROFILE.items():
                lam = (
                    profile["base_rate"]
                    * scale
                    * _growth_factor(day_offset, days, profile["recent_growth"])
                    * _surge_factor(day_offset, days, profile.get("surge"))
                )
                n_cases = int(rng.poisson(lam))
                for _ in range(n_cases):
                    records.append(
                        (
                            hospital["hospital_id"],
                            condition,
                            _random_age_for(condition, rng),
                            GENDERS[int(rng.choice(len(GENDERS), p=[0.49, 0.49, 0.02]))],
                            _random_severity_for(condition, rng),
                            case_date.isoformat(),
                        )
                    )

    conn.executemany(
        """
        INSERT INTO healthcare_cases
            (hospital_id, condition, age, gender, severity, case_date)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        records,
    )
    return len(records)


def seed_hospital_queue(conn, hospitals, days=28):
    """
    Generate hourly queue observations for the last `days` days.
    This is the training data for the ML crowd model.
    """
    rng = np.random.default_rng(RANDOM_SEED + 1)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    records = []

    for hospital in hospitals:
        scale = HOSPITAL_SCALE.get(hospital["hospital_name"], 1.0)
        base_load = 26 * scale
        minutes_per_patient = 1.6 if scale >= 1.0 else 2.1

        for day_offset in range(days, -1, -1):
            day = now.date() - timedelta(days=day_offset)
            for hour in OPERATING_HOURS:
                recorded_at = datetime.combine(day, datetime.min.time()).replace(hour=hour)
                if recorded_at > now:
                    continue

                expected = base_load * _crowd_shape(hour, recorded_at.weekday())
                noise = rng.normal(0, max(expected * 0.16, 1.5))
                patients = int(max(0, round(expected + noise)))

                # Waiting time grows with the queue, plus small random variation
                minutes = int(
                    max(
                        5,
                        round(
                            patients * minutes_per_patient
                            + rng.normal(6, 3)
                        ),
                    )
                )
                records.append(
                    (
                        hospital["hospital_id"],
                        recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
                        patients,
                        minutes,
                    )
                )

    conn.executemany(
        """
        INSERT INTO hospital_queue
            (hospital_id, recorded_at, patients_waiting, estimated_waiting_minutes)
        VALUES (?, ?, ?, ?);
        """,
        records,
    )
    return len(records)


def seed_all(case_days=120, queue_days=28):
    """Create the schema (if needed) and populate all demo data."""
    random.seed(RANDOM_SEED)
    init_db()

    with connection_scope() as conn:
        hospitals = seed_hospitals(conn)
        seed_health_information(conn)
        n_cases = seed_healthcare_cases(conn, hospitals, days=case_days)
        n_queue = seed_hospital_queue(conn, hospitals, days=queue_days)

    return {
        "hospitals": len(hospitals),
        "cases": n_cases,
        "queue_records": n_queue,
        "conditions": len(CONDITION_PROFILE),
    }


def reset_and_seed():
    """Wipe all demo data and regenerate it (used by the Admin page)."""
    init_db()
    with connection_scope() as conn:
        conn.execute("DELETE FROM crowd_predictions;")
        conn.execute("DELETE FROM hospital_queue;")
        conn.execute("DELETE FROM healthcare_cases;")
        conn.execute("DELETE FROM health_information;")
        conn.execute("DELETE FROM hospitals;")
    return seed_all()


if __name__ == "__main__":
    summary = reset_and_seed()
    print("Seeded demo database:")
    for key, value in summary.items():
        print(f"  {key:>15}: {value}")
