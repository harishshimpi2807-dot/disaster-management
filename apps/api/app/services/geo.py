from __future__ import annotations

import math
from typing import Any


def centroid(geojson: dict[str, Any] | None) -> tuple[float, float] | None:
    if not geojson:
        return None
    coords: list[tuple[float, float]] = []
    _collect(geojson, coords)
    if not coords:
        return None
    lng = sum(c[0] for c in coords) / len(coords)
    lat = sum(c[1] for c in coords) / len(coords)
    return lng, lat


def _collect(obj: Any, out: list[tuple[float, float]]) -> None:
    if isinstance(obj, dict):
        if obj.get("type") == "Point" and isinstance(obj.get("coordinates"), list):
            c = obj["coordinates"]
            out.append((float(c[0]), float(c[1])))
        else:
            for v in obj.values():
                _collect(v, out)
    elif isinstance(obj, list):
        if len(obj) >= 2 and isinstance(obj[0], (int, float)) and isinstance(obj[1], (int, float)):
            out.append((float(obj[0]), float(obj[1])))
        else:
            for v in obj:
                _collect(v, out)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lng1, lat1 = a
    lng2, lat2 = b
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1, math.sqrt(h)))


def point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


def geometry_intersects_bbox(geojson: dict[str, Any] | None, bbox: tuple[float, float, float, float]) -> bool:
    c = centroid(geojson)
    if not c:
        return False
    minx, miny, maxx, maxy = bbox
    return minx <= c[0] <= maxx and miny <= c[1] <= maxy


def point_in_geojson(point: tuple[float, float], geojson: dict[str, Any] | None) -> bool:
    if not geojson:
        return False
    gtype = geojson.get("type")
    if gtype == "Feature":
        return point_in_geojson(point, geojson.get("geometry"))
    if gtype == "FeatureCollection":
        return any(point_in_geojson(point, f) for f in geojson.get("features", []))
    if gtype == "Polygon":
        rings = geojson.get("coordinates") or []
        if not rings:
            return False
        if not point_in_ring(point, rings[0]):
            return False
        for hole in rings[1:]:
            if point_in_ring(point, hole):
                return False
        return True
    if gtype == "MultiPolygon":
        return any(point_in_geojson(point, {"type": "Polygon", "coordinates": p}) for p in geojson.get("coordinates", []))
    c = centroid(geojson)
    return bool(c and haversine_km(point, c) < 2)


def approx_area_ha(geojson: dict[str, Any] | None) -> float:
    coords: list[tuple[float, float]] = []
    _collect(geojson, coords)
    if len(coords) < 3:
        return 0.0
    # Shoelace in degrees, crude conversion near India (~111km)
    area = 0.0
    for i in range(len(coords)):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % len(coords)]
        area += x1 * y2 - x2 * y1
    area = abs(area) / 2.0
    km2 = area * 111 * 111 * math.cos(math.radians(sum(c[1] for c in coords) / len(coords)))
    return round(km2 * 100, 2)
