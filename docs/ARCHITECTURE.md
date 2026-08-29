# Sentinel Recovery — Product Architecture

Decision-support platform for disaster damage, fund verification, and recovery monitoring.
AI produces scores and recommendations. Humans make decisions. The system never approves or rejects funds or claims.

## Roles (least privilege)

| Role | Purpose |
|---|---|
| `system_admin` | Users, roles, parameters, datasets, notification rules, all audit |
| `gov_admin` | Disaster cases, regional damage, fund review, assign verification, recovery, reports |
| `field_officer` | Assigned inspections, geotagged evidence, verification reports |
| `agri_officer` | Crop-loss cases, satellite comparison, request verification |
| `auditor` | Claims, anomalies, potential duplicates, utilization, exports (read-heavy) |

## Lifecycle

Disaster → Damage assessment → Claim/fund verification → Anomaly & potential-duplicate review → Human decision support → Utilization evidence → Recovery monitoring

## Services

- **Web** (`apps/web`): Next.js App Router, MapLibre GIS, role-aware navigation
- **API** (`apps/api`): FastAPI, JWT, RBAC, REST `/api/v1`
- **Jobs**: persisted `AnalysisJob` rows; worker loop in-process (replaceable with Redis/Celery)
- **AI providers**: protocol classes in `app/ai/` — mock implementations by default
- **Storage**: local disk or S3-compatible (`STORAGE_BACKEND`)

## Spatial model

Geometries stored as GeoJSON (`json`) plus optional WKT. Bounding-box and point-in-polygon checks run in application code so SQLite demos work. With PostgreSQL/PostGIS, the same GeoJSON is queryable; compose file provisions PostGIS.

## Five operational questions

1. What was damaged?
2. Does the reported requirement match evidence?
3. Which cases need human verification?
4. What happened after funds were allocated?
5. Has the area recovered?
