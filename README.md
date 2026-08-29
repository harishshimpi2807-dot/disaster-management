# Sentinel Recovery

AI-assisted **disaster damage, fund verification, and recovery monitoring** for authorised government and institutional users.

The platform is **decision support**. Models produce risk scores, confidence, damage estimates, anomaly-risk alerts, and verification recommendations. Humans make every financial decision. The system never approves or rejects funds or insurance claims, and never labels a person as fraudulent.

## What it answers

1. What was damaged?
2. Does the reported claim or fund requirement match evidence?
3. Which cases need further human verification?
4. What happened after funds were allocated?
5. Has the affected area recovered?

## Stack

| Layer | Choice |
|---|---|
| Web | Next.js 15, TypeScript, MapLibre |
| API | FastAPI, JWT, RBAC |
| Data | SQLite for local demo; PostgreSQL/PostGIS via Docker |
| Files | Local disk (`data/uploads`) or S3/MinIO |
| AI | Protocol classes in `apps/api/app/ai/` — mock providers by default |

## Quick start (local demo)

Requires Python 3.11+ and Node 20+.

```bash
cp .env.example .env

cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Demonstration accounts

| Email | Password | Role |
|---|---|---|
| gov@sentinel.gov | ChangeMe!Gov12 | Government administrator |
| field@sentinel.gov | ChangeMe!Field12 | Field officer |
| agri@sentinel.gov | ChangeMe!Agri12 | Agricultural / insurance officer |
| audit@sentinel.gov | ChangeMe!Audit12 | Auditor |
| admin@sentinel.gov | ChangeMe!Admin12 | System administrator |

Change these passwords before any shared or production use. Seed data includes a Konkan flood, a cyclone case, recovery series, an assigned inspection, anomaly-risk alerts, and a potential-duplicate pair.

## Docker (PostGIS + MinIO + API + web)

```bash
docker compose up --build
```

Set `DATABASE_URL` in `.env` to the Compose Postgres URL if you run the API on the host against Compose Postgres.

## Tests

```bash
cd apps/api
source .venv/bin/activate
pytest
```

## API

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Prefix: `/api/v1`

Auth: `POST /auth/login` with JSON `{ "email", "password" }` then `Authorization: Bearer <token>`.

## Replacing mock AI

Set environment URLs:

- `CHANGE_DETECTION_URL`
- `DAMAGE_CLASSIFIER_URL`

HTTP providers POST the analysis payload and expect JSON matching the mock return shape. Anomaly and duplicate engines live in `app/services/` and can call a model service later without UI changes.

## Security notes

- Passwords hashed with bcrypt; JWT sessions
- Role checks on mutating routes
- Upload type and size limits
- Audit log on writes, logins, and exports
- No secrets in git — use `.env`
- Treat beneficiary data as sensitive; least privilege by role

## Project layout

```
apps/api/     FastAPI application
apps/web/     Next.js workspace
docs/         Architecture notes
docker-compose.yml
```
