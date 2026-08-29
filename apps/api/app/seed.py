from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.entities import (
    AgriculturalClaim,
    AnomalyAlert,
    Asset,
    DamageAssessment,
    DisasterEvent,
    DuplicateMatch,
    FieldInspection,
    FundAllocation,
    FundRequest,
    Notification,
    NotificationRule,
    RecoveryRecord,
    Region,
    SystemSetting,
    User,
)
from app.models.enums import Role
from app.services.ids import public_id

NOW = datetime.now(timezone.utc)


def poly(lng: float, lat: float, d: float = 0.18) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lng - d, lat - d],
                [lng + d, lat - d],
                [lng + d, lat + d],
                [lng - d, lat + d],
                [lng - d, lat - d],
            ]
        ],
    }


def seed_if_empty(db: Session) -> None:
    users = [
        User(email="admin@sentinel.gov", full_name="System Administrator", hashed_password=hash_password("ChangeMe!Admin12"), role=Role.SYSTEM_ADMIN.value, agency="NIC"),
        User(email="gov@sentinel.gov", full_name="Priya Deshmukh", hashed_password=hash_password("ChangeMe!Gov12"), role=Role.GOV_ADMIN.value, agency="SDMA Maharashtra", district="Ratnagiri"),
        User(email="field@sentinel.gov", full_name="Rahul Patil", hashed_password=hash_password("ChangeMe!Field12"), role=Role.FIELD_OFFICER.value, agency="District Collectorate", district="Ratnagiri"),
        User(email="agri@sentinel.gov", full_name="Meera Kulkarni", hashed_password=hash_password("ChangeMe!Agri12"), role=Role.AGRI_OFFICER.value, agency="Agriculture Department", district="Ratnagiri"),
        User(email="audit@sentinel.gov", full_name="Arun Iyer", hashed_password=hash_password("ChangeMe!Audit12"), role=Role.AUDITOR.value, agency="Accountant General"),
    ]
    db.add_all(users)
    db.flush()
    admin, gov, field, agri, audit = users

    flood = DisasterEvent(
        public_id="DSE-KONKAN",
        name="Konkan Monsoon Flood 2026",
        disaster_type="flood",
        start_date=date(2026, 7, 12),
        end_date=date(2026, 7, 28),
        state="Maharashtra",
        district="Ratnagiri",
        locality="Chiplun–Khed belt",
        severity="severe",
        description="Prolonged monsoon rainfall caused riverine flooding along Vashishti, with inundated paddy and damaged rural roads.",
        status="monitoring",
        boundary=poly(73.52, 17.53, 0.22),
        created_by_id=gov.id,
    )
    cyclone = DisasterEvent(
        public_id="DSE-BAY01",
        name="Cyclone Nivar remnant rains",
        disaster_type="cyclone",
        start_date=date(2026, 6, 3),
        end_date=date(2026, 6, 8),
        state="Odisha",
        district="Puri",
        locality="Coastal blocks",
        severity="catastrophic",
        description="Cyclonic winds and storm surge affected coastal agriculture and critical facilities.",
        status="active",
        boundary=poly(85.83, 19.81, 0.2),
        created_by_id=gov.id,
    )
    quake = DisasterEvent(
        public_id="DSE-HIM01",
        name="Western Himalaya tremor",
        disaster_type="earthquake",
        start_date=date(2026, 4, 19),
        end_date=date(2026, 4, 19),
        state="Uttarakhand",
        district="Chamoli",
        locality="Joshimath vicinity",
        severity="moderate",
        description="Moderate tremor with localised building and road damage. Used for recovery comparison.",
        status="closed",
        boundary=poly(79.56, 30.55, 0.12),
        created_by_id=gov.id,
    )
    db.add_all([flood, cyclone, quake])
    db.flush()

    assessments = [
        DamageAssessment(public_id=public_id("DAS"), disaster_id=flood.id, category="flooded_areas", severity="severe", estimated_area_ha=1840, confidence=0.82, geometry=poly(73.51, 17.54, 0.12), notes="NDWI-style water expansion versus pre-monsoon mosaic.", analyzed_at=NOW, created_by_id=gov.id),
        DamageAssessment(public_id=public_id("DAS"), disaster_id=flood.id, category="agricultural_fields", severity="severe", estimated_area_ha=960, confidence=0.76, geometry=poly(73.48, 17.50, 0.1), notes="Standing paddy inundation.", analyzed_at=NOW, created_by_id=gov.id),
        DamageAssessment(public_id=public_id("DAS"), disaster_id=flood.id, category="roads", severity="moderate", estimated_area_ha=42, confidence=0.71, geometry=poly(73.55, 17.56, 0.06), notes="Washouts on village connectors.", analyzed_at=NOW, created_by_id=gov.id),
        DamageAssessment(public_id=public_id("DAS"), disaster_id=cyclone.id, category="buildings", severity="catastrophic", estimated_area_ha=118, confidence=0.69, geometry=poly(85.84, 19.80, 0.08), notes="Coastal housing stock change.", analyzed_at=NOW, created_by_id=gov.id),
        DamageAssessment(public_id=public_id("DAS"), disaster_id=cyclone.id, category="vegetation", severity="severe", estimated_area_ha=540, confidence=0.74, geometry=poly(85.81, 19.83, 0.1), notes="Canopy loss along the surge line.", analyzed_at=NOW, created_by_id=gov.id),
    ]
    db.add_all(assessments)
    db.flush()

    c1 = AgriculturalClaim(
        public_id="CLM-R001",
        disaster_id=flood.id,
        farmer_reference="KISAN-4471",
        crop_type="Paddy",
        incident_date=date(2026, 7, 14),
        reported_damage_pct=80,
        estimated_damage_pct=62,
        confidence=0.74,
        difference_pct=18,
        recommendation="Assign human field verification before any financial recommendation.",
        status="requires_verification",
        field_boundary=poly(73.50, 17.52, 0.03),
        historical_condition="Healthy vegetative stage in June mosaic.",
        post_condition="Standing water visible in July mosaic.",
        created_by_id=agri.id,
    )
    c2 = AgriculturalClaim(
        public_id="CLM-R002",
        disaster_id=flood.id,
        farmer_reference="KISAN-4471",
        crop_type="Paddy",
        incident_date=date(2026, 7, 15),
        reported_damage_pct=78,
        estimated_damage_pct=60,
        confidence=0.72,
        difference_pct=18,
        recommendation="Potential overlap with nearby parcel. Review as a potential duplicate, not an accusation.",
        status="requires_verification",
        field_boundary=poly(73.501, 17.521, 0.03),
        created_by_id=agri.id,
    )
    c3 = AgriculturalClaim(
        public_id="CLM-R003",
        disaster_id=flood.id,
        farmer_reference="KISAN-8820",
        crop_type="Mango",
        incident_date=date(2026, 7, 16),
        reported_damage_pct=35,
        estimated_damage_pct=32,
        confidence=0.81,
        difference_pct=3,
        recommendation="Reported loss is aligned with the remote-sensing estimate. Continue documentary review. Do not treat this as an approval.",
        status="consistent",
        field_boundary=poly(73.58, 17.49, 0.025),
        created_by_id=agri.id,
    )
    c4 = AgriculturalClaim(
        public_id="CLM-O001",
        disaster_id=cyclone.id,
        farmer_reference="KISAN-1102",
        crop_type="Coconut",
        incident_date=date(2026, 6, 4),
        reported_damage_pct=95,
        estimated_damage_pct=48,
        confidence=0.66,
        difference_pct=47,
        recommendation="High anomaly risk. Escalate for independent verification. This is not a finding of fraud.",
        status="high_anomaly_risk",
        field_boundary=poly(85.90, 19.78, 0.04),
        created_by_id=agri.id,
    )
    db.add_all([c1, c2, c3, c4])
    db.flush()

    fr1 = FundRequest(
        public_id="FND-PWD1",
        disaster_id=flood.id,
        department="Public Works",
        location_label="Chiplun rural roads",
        damage_category="roads",
        reported_damage="14 km of rural roads washed out",
        requested_amount=18_40_00_000,
        evidence_consistency=58,
        confidence=0.7,
        recommendation="Evidence is incomplete or mixed. Request field verification before a funding recommendation.",
        status="requires_additional_verification",
        geometry=poly(73.55, 17.56, 0.05),
        created_by_id=gov.id,
    )
    fr2 = FundRequest(
        public_id="FND-AGR1",
        disaster_id=flood.id,
        department="Agriculture",
        location_label="Khed paddy belt",
        damage_category="agricultural_fields",
        reported_damage="Input support for 2,100 ha",
        requested_amount=9_20_00_000,
        evidence_consistency=78,
        confidence=0.77,
        recommendation="Geospatial evidence is broadly consistent with the reported requirement. Human officials remain the decision-makers.",
        status="consistent_with_evidence",
        geometry=poly(73.48, 17.50, 0.08),
        created_by_id=gov.id,
    )
    db.add_all([fr1, fr2])
    db.flush()

    al1 = FundAllocation(
        public_id="ALC-RD01",
        disaster_id=flood.id,
        fund_request_id=fr1.id,
        purpose="Emergency road restoration — Chiplun connectors",
        amount=6_00_00_000,
        allocating_authority="State Relief Commissioner",
        implementing_agency="PWD Ratnagiri",
        location_label="Chiplun",
        allocated_on=date(2026, 8, 1),
        expected_completion=date(2026, 10, 15),
        status="delayed",
        planned_progress_pct=55,
        observed_progress_pct=28,
        geometry=poly(73.55, 17.56, 0.04),
        created_by_id=gov.id,
    )
    al2 = FundAllocation(
        public_id="ALC-AG01",
        disaster_id=flood.id,
        fund_request_id=fr2.id,
        purpose="Seed and input support — Khed",
        amount=4_50_00_000,
        allocating_authority="State Relief Commissioner",
        implementing_agency="Agriculture Department",
        location_label="Khed",
        allocated_on=date(2026, 8, 4),
        expected_completion=date(2026, 9, 30),
        status="in_progress",
        planned_progress_pct=40,
        observed_progress_pct=38,
        geometry=poly(73.48, 17.50, 0.05),
        created_by_id=gov.id,
    )
    db.add_all([al1, al2])

    db.add_all(
        [
            AnomalyAlert(
                public_id="ANM-001",
                disaster_id=cyclone.id,
                entity_type="claim",
                entity_id=c4.id,
                risk_level="high",
                risk_score=78,
                reasons=["Significant difference between reported damage and remote-sensing estimate"],
                recommended_action="Assign field verification and retain the case in the review queue.",
                geometry=c4.field_boundary,
            ),
            AnomalyAlert(
                public_id="ANM-002",
                disaster_id=flood.id,
                entity_type="fund_request",
                entity_id=fr1.id,
                risk_level="medium",
                risk_score=48,
                reasons=["Requested amount is elevated versus similar records"],
                recommended_action="Request additional evidence and a second officer review.",
                geometry=fr1.geometry,
            ),
        ]
    )
    db.add(
        DuplicateMatch(
            public_id="DUP-001",
            left_type="claim",
            left_id=c1.id,
            right_type="claim",
            right_id=c2.id,
            similarity=86,
            matching_factors=["Same or nearly identical location", "Same disaster event", "Matching claim/case reference"],
            review_status="open",
        )
    )

    ins = FieldInspection(
        public_id="INS-441",
        disaster_id=flood.id,
        case_type="claim",
        case_id=c1.id,
        assigned_to_id=field.id,
        assigned_by_id=gov.id,
        status="assigned",
        required_actions="Photograph standing crop, record water marks, confirm parcel boundary with farmer reference KISAN-4471.",
        location={"type": "Point", "coordinates": [73.50, 17.52]},
    )
    db.add(ins)

    recs = [
        RecoveryRecord(public_id=public_id("RCV"), disaster_id=flood.id, category="roads", state="Maharashtra", district="Ratnagiri", locality="Chiplun", recovery_pct=100, recovery_score=100, status="not_started", phase="pre_disaster", geometry=poly(73.55, 17.56, 0.04), observed_on=date(2026, 6, 1), notes="Baseline road network intact."),
        RecoveryRecord(public_id=public_id("RCV"), disaster_id=flood.id, category="roads", state="Maharashtra", district="Ratnagiri", locality="Chiplun", recovery_pct=8, recovery_score=8, status="early", phase="post_disaster", geometry=poly(73.55, 17.56, 0.04), observed_on=date(2026, 7, 30)),
        RecoveryRecord(public_id=public_id("RCV"), disaster_id=flood.id, category="roads", state="Maharashtra", district="Ratnagiri", locality="Chiplun", recovery_pct=18, recovery_score=16, status="early", phase="month_1", geometry=poly(73.55, 17.56, 0.04), observed_on=date(2026, 8, 12)),
        RecoveryRecord(public_id=public_id("RCV"), disaster_id=flood.id, category="roads", state="Maharashtra", district="Ratnagiri", locality="Chiplun", recovery_pct=28, recovery_score=26, status="delayed", phase="month_3", geometry=poly(73.55, 17.56, 0.04), observed_on=date(2026, 8, 20), notes="Embankment still unstable."),
        RecoveryRecord(public_id=public_id("RCV"), disaster_id=flood.id, category="agricultural_fields", state="Maharashtra", district="Ratnagiri", locality="Khed", recovery_pct=44, recovery_score=42, status="underway", phase="month_1", geometry=poly(73.48, 17.50, 0.06), observed_on=date(2026, 8, 20)),
        RecoveryRecord(public_id=public_id("RCV"), disaster_id=flood.id, category="flooded_areas", state="Maharashtra", district="Ratnagiri", locality="Vashishti banks", recovery_pct=71, recovery_score=68, status="advanced", phase="current", geometry=poly(73.51, 17.54, 0.08), observed_on=date(2026, 8, 22)),
        RecoveryRecord(public_id=public_id("RCV"), disaster_id=cyclone.id, category="buildings", state="Odisha", district="Puri", locality="Coastal blocks", recovery_pct=22, recovery_score=20, status="early", phase="post_disaster", geometry=poly(85.84, 19.80, 0.07), observed_on=date(2026, 8, 10)),
        RecoveryRecord(public_id=public_id("RCV"), disaster_id=quake.id, category="buildings", state="Uttarakhand", district="Chamoli", locality="Joshimath", recovery_pct=81, recovery_score=80, status="advanced", phase="current", geometry=poly(79.56, 30.55, 0.05), observed_on=date(2026, 8, 1)),
    ]
    db.add_all(recs)
    db.add_all(
        [
            Region(state="Maharashtra", district="Ratnagiri", locality="Chiplun–Khed belt", geometry=poly(73.52, 17.53, 0.22)),
            Region(state="Odisha", district="Puri", locality="Coastal blocks", geometry=poly(85.83, 19.81, 0.2)),
            Region(state="Uttarakhand", district="Chamoli", locality="Joshimath vicinity", geometry=poly(79.56, 30.55, 0.12)),
            Asset(public_id=public_id("AST"), kind="bridge", label="Vashishti connector", disaster_id=flood.id, geometry=poly(73.55, 17.56, 0.02)),
            Asset(public_id=public_id("AST"), kind="parcel", label="KISAN-4471 holding", disaster_id=flood.id, geometry=poly(73.50, 17.52, 0.03)),
        ]
    )

    db.add_all(
        [
            SystemSetting(key="anomaly_high_threshold", value="65"),
            SystemSetting(key="duplicate_similarity_threshold", value="55"),
            SystemSetting(key="max_upload_mb", value="25"),
        ]
    )
    db.add(NotificationRule(name="High anomaly risk", event_type="anomaly", min_risk="high", channel="in_app", enabled=True))
    db.add_all(
        [
            Notification(user_id=gov.id, title="Delayed allocation — Chiplun roads", body="ALC-RD01 observed progress is behind plan.", link="/app/funds/allocations"),
            Notification(user_id=field.id, title="Inspection assigned", body="INS-441 requires field verification in Chiplun.", link="/app/inspections/"),
            Notification(user_id=agri.id, title="Potential duplicate crop-loss records", body="CLM-R001 and CLM-R002 share location and farmer reference.", link="/app/duplicates"),
        ]
    )
    db.commit()
