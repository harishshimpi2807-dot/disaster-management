from app.services.anomaly import evaluate_claim_or_request
from app.services.duplicates import similarity
from datetime import date


def test_high_delta_is_anomaly_risk_not_fraud_label():
    r = evaluate_claim_or_request(
        reported=90,
        estimated=30,
        amount=None,
        incident=date(2026, 7, 1),
        disaster_start=date(2026, 7, 1),
        disaster_end=date(2026, 7, 10),
        geometry=None,
        disaster_boundary=None,
    )
    assert r["risk_level"] in {"high", "critical", "medium"}
    assert "fraud" not in r["recommended_action"].lower()


def test_potential_duplicate_language():
    score, factors = similarity(
        a_geo={"type": "Point", "coordinates": [73.5, 17.5]},
        b_geo={"type": "Point", "coordinates": [73.5005, 17.5004]},
        a_disaster=1,
        b_disaster=1,
        a_cat="agricultural_fields",
        b_cat="agricultural_fields",
        a_ref="KISAN-1",
        b_ref="KISAN-1",
        a_date=date(2026, 7, 1),
        b_date=date(2026, 7, 2),
    )
    assert score >= 55
    assert any("location" in f.lower() or "identical" in f.lower() for f in factors)
