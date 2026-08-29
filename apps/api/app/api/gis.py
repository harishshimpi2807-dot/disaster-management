from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentUser, Db
from app.models.entities import (
    AgriculturalClaim,
    AnomalyAlert,
    DamageAssessment,
    DisasterEvent,
    DuplicateMatch,
    FieldInspection,
    FundAllocation,
    FundRequest,
    RecoveryRecord,
)
from app.services.geo import centroid

router = APIRouter(tags=["gis"])


def _feat(geom, props):
    if not geom:
        return None
    if geom.get("type") == "Feature":
        return {**geom, "properties": {**(geom.get("properties") or {}), **props}}
    g = geom.get("geometry") if geom.get("type") == "FeatureCollection" else geom
    if geom.get("type") == "FeatureCollection":
        return None
    return {"type": "Feature", "geometry": g, "properties": props}


def _point(geom, props):
    c = centroid(geom)
    if not c:
        return None
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [c[0], c[1]]}, "properties": props}


@router.get("/gis/layers")
def layers(
    db: Db,
    user: CurrentUser,
    disaster_id: int | None = None,
    disasters: bool = True,
    damage: bool = True,
    claims: bool = True,
    funds: bool = True,
    allocations: bool = True,
    anomalies: bool = True,
    duplicates: bool = True,
    recovery: bool = True,
    inspections: bool = True,
):
    collections: dict = {}

    def dfilter(q, col):
        return q.where(col == disaster_id) if disaster_id else q

    if disasters:
        stmt = select(DisasterEvent).where(DisasterEvent.deleted_at.is_(None))
        if disaster_id:
            stmt = stmt.where(DisasterEvent.id == disaster_id)
        feats = []
        for d in db.scalars(stmt).all():
            f = _feat(d.boundary, {"id": d.id, "kind": "disaster", "name": d.name, "severity": d.severity, "type": d.disaster_type, "public_id": d.public_id, "href": f"/app/disasters/{d.id}"})
            if f:
                feats.append(f)
        collections["disasters"] = {"type": "FeatureCollection", "features": feats}
    if damage:
        feats = []
        for a in db.scalars(dfilter(select(DamageAssessment), DamageAssessment.disaster_id)).all():
            f = _feat(a.geometry, {"id": a.id, "kind": "damage", "category": a.category, "severity": a.severity, "public_id": a.public_id})
            if f:
                feats.append(f)
        collections["damage"] = {"type": "FeatureCollection", "features": feats}
    if claims:
        feats = []
        for c in db.scalars(dfilter(select(AgriculturalClaim), AgriculturalClaim.disaster_id)).all():
            f = _feat(c.field_boundary, {"id": c.id, "kind": "claim", "status": c.status, "public_id": c.public_id, "reported": c.reported_damage_pct, "href": f"/app/claims/{c.id}"})
            if f:
                feats.append(f)
        collections["claims"] = {"type": "FeatureCollection", "features": feats}
    if funds:
        feats = []
        for r in db.scalars(dfilter(select(FundRequest), FundRequest.disaster_id)).all():
            f = _feat(r.geometry, {"id": r.id, "kind": "fund_request", "status": r.status, "amount": r.requested_amount, "public_id": r.public_id, "href": f"/app/funds/requests/{r.id}"})
            if f:
                feats.append(f)
        collections["fund_requests"] = {"type": "FeatureCollection", "features": feats}
    if allocations:
        feats = []
        for a in db.scalars(dfilter(select(FundAllocation), FundAllocation.disaster_id)).all():
            f = _feat(a.geometry, {"id": a.id, "kind": "allocation", "status": a.status, "public_id": a.public_id, "observed": a.observed_progress_pct})
            if f:
                feats.append(f)
        collections["allocations"] = {"type": "FeatureCollection", "features": feats}
    if anomalies:
        feats = []
        for a in db.scalars(dfilter(select(AnomalyAlert), AnomalyAlert.disaster_id)).all():
            f = _feat(a.geometry, {"id": a.id, "kind": "anomaly", "risk_level": a.risk_level, "risk_score": a.risk_score, "public_id": a.public_id, "href": "/app/anomalies"}) or _point(
                a.geometry, {"id": a.id, "kind": "anomaly", "risk_level": a.risk_level, "public_id": a.public_id}
            )
            if f:
                feats.append(f)
        collections["anomalies"] = {"type": "FeatureCollection", "features": feats}
    if recovery:
        feats = []
        for r in db.scalars(dfilter(select(RecoveryRecord), RecoveryRecord.disaster_id)).all():
            f = _feat(r.geometry, {"id": r.id, "kind": "recovery", "status": r.status, "pct": r.recovery_pct, "public_id": r.public_id})
            if f:
                feats.append(f)
        collections["recovery"] = {"type": "FeatureCollection", "features": feats}
    if inspections:
        feats = []
        for i in db.scalars(dfilter(select(FieldInspection), FieldInspection.disaster_id)).all():
            f = _feat(i.location, {"id": i.id, "kind": "inspection", "status": i.status, "public_id": i.public_id, "href": f"/app/inspections/{i.id}"}) or _point(
                i.location, {"id": i.id, "kind": "inspection", "status": i.status, "public_id": i.public_id, "href": f"/app/inspections/{i.id}"}
            )
            if f:
                feats.append(f)
        collections["inspections"] = {"type": "FeatureCollection", "features": feats}
    if duplicates:
        feats = []
        for d in db.scalars(select(DuplicateMatch).where(DuplicateMatch.review_status == "open")).all():
            left = db.get(AgriculturalClaim, d.left_id) if d.left_type == "claim" else None
            right = db.get(AgriculturalClaim, d.right_id) if d.right_type == "claim" else None
            ca = centroid(left.field_boundary) if left else None
            cb = centroid(right.field_boundary) if right else None
            if ca and cb:
                feats.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": [list(ca), list(cb)]},
                        "properties": {
                            "id": d.id,
                            "kind": "potential_duplicate",
                            "public_id": d.public_id,
                            "similarity": d.similarity,
                            "href": "/app/duplicates",
                        },
                    }
                )
        collections["duplicates"] = {"type": "FeatureCollection", "features": feats, "open_count": len(feats)}
    return collections
