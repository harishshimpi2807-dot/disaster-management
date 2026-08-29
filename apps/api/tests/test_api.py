from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_login_and_overview():
    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", json={"email": "gov@sentinel.gov", "password": "ChangeMe!Gov12"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        ov = client.get("/api/v1/analytics/overview", headers=h)
        assert ov.status_code == 200
        body = ov.json()
        assert body["total_disasters"] >= 1
        gis = client.get("/api/v1/gis/layers", headers=h)
        assert gis.status_code == 200
        body_gis = gis.json()
        assert "disasters" in body_gis
        assert "features" in body_gis["duplicates"]
        delayed = client.get("/api/v1/recovery/alerts/delayed", headers=h)
        assert delayed.status_code == 200
        assert isinstance(delayed.json(), list)


def test_disaster_dossier_and_claim_verification():
    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", json={"email": "gov@sentinel.gov", "password": "ChangeMe!Gov12"})
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        disasters = client.get("/api/v1/disasters", headers=h).json()
        did = disasters[0]["id"]
        dossier = client.get(f"/api/v1/disasters/{did}/dossier", headers=h)
        assert dossier.status_code == 200
        assert "claims" in dossier.json()
        claims = client.get("/api/v1/claims", headers=h).json()
        cid = claims[0]["id"]
        req = client.post(f"/api/v1/claims/{cid}/request-verification", headers=h)
        assert req.status_code == 200
        assert req.json()["inspection_id"]
        logout = client.post("/api/v1/auth/logout", headers=h)
        assert logout.status_code == 200


def test_archive_is_soft_delete():
    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", json={"email": "gov@sentinel.gov", "password": "ChangeMe!Gov12"})
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        created = client.post(
            "/api/v1/disasters",
            headers=h,
            json={
                "name": "Test archive event",
                "disaster_type": "flood",
                "start_date": "2026-08-01",
                "state": "Goa",
                "district": "North Goa",
                "severity": "minor",
                "description": "Temporary",
                "status": "draft",
            },
        )
        assert created.status_code == 200, created.text
        nid = created.json()["id"]
        gone = client.delete(f"/api/v1/disasters/{nid}", headers=h)
        assert gone.status_code == 200
        missing = client.get(f"/api/v1/disasters/{nid}", headers=h)
        assert missing.status_code == 404


def test_field_officer_sees_assigned_only():
    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", json={"email": "field@sentinel.gov", "password": "ChangeMe!Field12"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        ins = client.get("/api/v1/inspections", headers={"Authorization": f"Bearer {token}"})
        assert ins.status_code == 200
        assert len(ins.json()) >= 1
