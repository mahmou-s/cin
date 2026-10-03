# CIN v2.0 — Production Demonstration Runbook

## Prerequisites

- Docker Engine + Docker Compose v2
- A DNS name or server IP
- TLS termination at the cloud load balancer/reverse proxy for public demonstrations

## 1. Configure environment

```bash
cp .env.example .env
```

Set strong secrets and replace:

- `NEXT_PUBLIC_API_URL`
- `CORS_ORIGINS`
- PostgreSQL password
- Neo4j password
- Redis password

## 2. Start the stack

```bash
docker compose --env-file .env up --build -d
```

The startup order is:

```text
PostgreSQL / Neo4j / Redis
        ↓
      Alembic
        ↓
       API
        ↓
       Web

Worker starts alongside API after migration + Redis + Neo4j health checks.
```

## 3. Verify health

```bash
curl http://SERVER:8000/health
curl http://SERVER:8000/health/ready
```

`/health/ready` must report PostgreSQL, Redis and Neo4j as `ok`.

## 4. Load the demonstrator

```bash
python3 seed_civilization.py --api https://api.example.com/api/v1
```

The seed uses the normal submission and review endpoints. It does not write directly to Neo4j.

## 5. Demonstration flow

1. Open the Next.js application.
2. Show the interactive graph.
3. Show the verified capability assertions.
4. Show evidence and confidence.
5. Show the opportunity-path explorer.
6. Explain the path as an analytical hypothesis, not an automated investment decision.

## 6. Operational checks

```bash
docker compose ps
docker compose logs --tail=100 api
docker compose logs --tail=100 worker
docker compose logs --tail=100 migration
```

## 7. Reproducibility

The demonstrator can be rebuilt from PostgreSQL verified facts. Neo4j is a projection and should not be treated as the authoritative store.
