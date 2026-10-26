"""
Root wrapper for prediction engine. Provides backward compatibility for
any scripts or modules importing from prediction directly.
"""

from src.prediction import predict_hospital, load_models

__all__ = ["predict_hospital", "load_models"]

if __name__ == "__main__":
    print("=" * 60)
    print("CONNECTED HEALTHCARE — PREDICTION ENGINE TEST")
    print("=" * 60)
    hospitals = [
        "Apollo Hospital",
        "Government General Hospital",
        "Sri Venkateswara Hospital"
    ]
    for hospital in hospitals:
        try:
            res = predict_hospital(hospital)
            print(f"\nHospital: {res['hospital']} ({res['location']})")
            print(f"Recorded At: {res['recorded_at']}")
            print(f"Current Crowd: {res['current_crowd']} -> Predicted Next: {res['predicted_crowd']} (delta: {res['crowd_delta']:+d})")
            print(f"Current Wait : {res['current_waiting_minutes']} min -> Predicted Next: {res['predicted_waiting_minutes']} min (delta: {res['waiting_delta']:+d})")
            print(f"Model: {res['model_type']}")
        except Exception as e:
            print(f"Error forecasting {hospital}: {e}")