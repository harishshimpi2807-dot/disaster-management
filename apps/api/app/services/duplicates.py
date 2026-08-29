from __future__ import annotations

from datetime import date
from typing import Any

from app.services.geo import centroid, haversine_km


def similarity(
    *,
    a_geo: dict[str, Any] | None,
    b_geo: dict[str, Any] | None,
    a_disaster: int,
    b_disaster: int,
    a_cat: str,
    b_cat: str,
    a_ref: str,
    b_ref: str,
    a_date: date | None,
    b_date: date | None,
    a_asset: str = "",
    b_asset: str = "",
) -> tuple[float, list[str]]:
    """Potential-duplicate scoring. Does not assert wrongdoing."""
    factors: list[str] = []
    score = 0.0
    ca, cb = centroid(a_geo), centroid(b_geo)
    if ca and cb:
        d = haversine_km(ca, cb)
        if d < 0.15:
            score += 40
            factors.append("Same or nearly identical location")
        elif d < 0.6:
            score += 24
            factors.append("Nearby location")
        elif d < 2:
            score += 10
            factors.append("Same locality-scale coordinates")
    if a_disaster == b_disaster:
        score += 18
        factors.append("Same disaster event")
    if a_cat and a_cat == b_cat:
        score += 12
        factors.append("Same damage category")
    if a_asset and a_asset == b_asset:
        score += 22
        factors.append("Same asset identifier")
    if a_ref and b_ref and a_ref.strip().lower() == b_ref.strip().lower():
        score += 16
        factors.append("Matching claim/case reference")
    if a_date and b_date and abs((a_date - b_date).days) <= 14:
        score += 10
        factors.append("Close incident dates")
    return min(99.0, round(score, 1)), factors
