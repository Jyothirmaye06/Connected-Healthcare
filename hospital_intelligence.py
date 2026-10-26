from prediction import predict_hospital
from anomaly_detection import (
    load_data,
    create_anomaly_features,
    detect_anomalies,
    generate_status
)


# ---------------------------------------------------------
# GET HOSPITAL INTELLIGENCE
# ---------------------------------------------------------

def get_hospital_intelligence(hospital_name):

    # ---------------------------------------------
    # 1. ML PREDICTIONS
    # ---------------------------------------------

    prediction = predict_hospital(
        hospital_name
    )

    # ---------------------------------------------
    # 2. LOAD ANOMALY DATA
    # ---------------------------------------------

    df = load_data()

    df = create_anomaly_features(df)

    anomaly_data = detect_anomalies(df)

    hospital_data = anomaly_data[
        anomaly_data["hospital"] == hospital_name
    ]

    if hospital_data.empty:
        raise ValueError(
            f"No anomaly data found for {hospital_name}"
        )

    latest = (
        hospital_data
        .sort_values("recorded_at")
        .iloc[-1]
    )

    # ---------------------------------------------
    # 3. OPERATIONAL STATUS
    # ---------------------------------------------

    status, reasons = generate_status(
        latest
    )

    # ---------------------------------------------
    # 4. COMBINE EVERYTHING
    # ---------------------------------------------

    intelligence = {

        "hospital": hospital_name,

        "location": prediction["location"],

        "recorded_at": prediction["recorded_at"],

        # Current situation
        "current_crowd":
            prediction["current_crowd"],

        "current_waiting_minutes":
            prediction[
                "current_waiting_minutes"
            ],

        "new_patients":
            prediction["new_patients"],

        "discharged_patients":
            prediction[
                "discharged_patients"
            ],

        "emergency_cases":
            prediction["emergency_cases"],

        # Predictions
        "predicted_crowd":
            prediction["predicted_crowd"],

        "predicted_waiting_minutes":
            prediction[
                "predicted_waiting_minutes"
            ],

        # Anomaly information
        "recent_average":
            round(
                float(
                    latest["rolling_avg_3"]
                ),
                1
            ),

        "crowd_deviation":
            round(
                float(
                    latest["crowd_deviation"]
                ),
                1
            ),

        "anomaly_score":
            round(
                float(
                    latest["anomaly_score"]
                ),
                4
            ),

        # Final status
        "status":
            status,

        "reasons":
            reasons
    }

    return intelligence


# ---------------------------------------------------------
# TEST ENGINE
# ---------------------------------------------------------

if __name__ == "__main__":

    hospitals = [
        "Apollo Hospital",
        "Government General Hospital",
        "Sri Venkateswara Hospital"
    ]

    print(
        "CONNECTED HEALTHCARE"
    )

    print(
        "UNIFIED HOSPITAL INTELLIGENCE ENGINE"
    )

    print("=" * 70)

    for hospital in hospitals:

        try:

            result = get_hospital_intelligence(
                hospital
            )

            print(
                "\nHospital:",
                result["hospital"]
            )

            print(
                "Location:",
                result["location"]
            )

            print(
                "Latest observation:",
                result["recorded_at"]
            )

            print(
                "\nCURRENT STATUS"
            )

            print(
                "Current crowd:",
                result["current_crowd"]
            )

            print(
                "Current waiting:",
                result[
                    "current_waiting_minutes"
                ],
                "minutes"
            )

            print(
                "New patients:",
                result["new_patients"]
            )

            print(
                "Emergency cases:",
                result["emergency_cases"]
            )

            print(
                "\nML PREDICTION"
            )

            print(
                "Predicted next crowd:",
                result["predicted_crowd"]
            )

            print(
                "Predicted next waiting:",
                result[
                    "predicted_waiting_minutes"
                ],
                "minutes"
            )

            print(
                "\nANOMALY ANALYSIS"
            )

            print(
                "Recent average:",
                result["recent_average"]
            )

            print(
                "Crowd deviation:",
                result["crowd_deviation"]
            )

            print(
                "Anomaly score:",
                result["anomaly_score"]
            )

            print(
                "Operational status:",
                result["status"]
            )

            if result["reasons"]:

                print("Reasons:")

                for reason in result["reasons"]:
                    print(
                        " -",
                        reason
                    )

            else:

                print(
                    "Reasons: No unusual indicators"
                )

            print(
                "-" * 70
            )

        except Exception as e:

            print(
                f"Error for {hospital}: {e}"
            )