from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.services.geo import approx_area_ha


class ChangeDetectionProvider(ABC):
    @abstractmethod
    def detect(self, *, before_key: str | None, after_key: str | None, aoi: dict[str, Any] | None, disaster_type: str) -> dict[str, Any]:
        ...


class DamageClassifierProvider(ABC):
    @abstractmethod
    def classify(self, *, disaster_type: str, aoi: dict[str, Any] | None) -> list[dict[str, Any]]:
        ...


class MockChangeDetection(ChangeDetectionProvider):
    """Replace with CHANGE_DETECTION_URL HTTP client when a model service exists."""

    def detect(self, *, before_key: str | None, after_key: str | None, aoi: dict[str, Any] | None, disaster_type: str) -> dict[str, Any]:
        seed = hashlib.sha256(f"{before_key}:{after_key}:{disaster_type}".encode()).hexdigest()
        conf = 0.62 + (int(seed[:2], 16) / 255) * 0.32
        area = max(12.0, approx_area_ha(aoi) * (0.15 + (int(seed[2:4], 16) / 255) * 0.45))
        return {
            "provider": "mock_change_detection",
            "model_version": "heuristic-v1",
            "changed_area_ha": round(area, 2),
            "confidence": round(conf, 3),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Heuristic change envelope. Swap this provider for a real change-detection inference service.",
        }


class MockDamageClassifier(DamageClassifierProvider):
    def classify(self, *, disaster_type: str, aoi: dict[str, Any] | None) -> list[dict[str, Any]]:
        mapping = {
            "flood": ["flooded_areas", "agricultural_fields", "roads", "bridges", "buildings"],
            "cyclone": ["buildings", "vegetation", "infrastructure", "agricultural_fields"],
            "landslide": ["roads", "buildings", "vegetation"],
            "drought": ["agricultural_fields", "vegetation"],
            "earthquake": ["buildings", "critical_facilities", "infrastructure", "roads"],
            "wildfire": ["vegetation", "buildings", "agricultural_fields"],
        }
        cats = mapping.get(disaster_type, ["infrastructure", "buildings"])
        area = max(8.0, approx_area_ha(aoi) or 40)
        out = []
        for i, cat in enumerate(cats):
            share = 0.42 / (i + 1)
            out.append(
                {
                    "category": cat,
                    "severity": ["moderate", "severe", "catastrophic", "minor"][i % 4],
                    "estimated_area_ha": round(area * share, 2),
                    "confidence": round(0.71 - i * 0.06, 3),
                }
            )
        return out


def get_change_detection() -> ChangeDetectionProvider:
    settings = get_settings()
    if settings.change_detection_url:
        return HttpChangeDetection(settings.change_detection_url)
    return MockChangeDetection()


def get_damage_classifier() -> DamageClassifierProvider:
    settings = get_settings()
    if settings.damage_classifier_url:
        return HttpDamageClassifier(settings.damage_classifier_url)
    return MockDamageClassifier()


class HttpChangeDetection(ChangeDetectionProvider):
    def __init__(self, url: str):
        self.url = url

    def detect(self, **kwargs: Any) -> dict[str, Any]:
        import httpx

        r = httpx.post(self.url, json=kwargs, timeout=60)
        r.raise_for_status()
        return r.json()


class HttpDamageClassifier(DamageClassifierProvider):
    def __init__(self, url: str):
        self.url = url

    def classify(self, **kwargs: Any) -> list[dict[str, Any]]:
        import httpx

        r = httpx.post(self.url, json=kwargs, timeout=60)
        r.raise_for_status()
        return r.json()
