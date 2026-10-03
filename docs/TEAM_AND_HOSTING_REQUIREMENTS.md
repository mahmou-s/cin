# CIN Team & Hosting Requirements

## Minimum engineering team for controlled MVP

### 1. Technical Lead / Solution Architect
Owns architecture, boundaries, ADRs, release decisions and technical debt.

### 2. Backend + Database Engineer
Owns FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis queues and Neo4j projection.

### 3. Frontend Engineer
Owns Next.js/React, API integration, UX, accessibility and production build.

### 4. DevOps / Cloud Engineer
Owns Docker, CI/CD, environments, secrets, TLS, backups, observability and deployment.

### 5. QA / Test Engineer
Owns integration, E2E, regression, test data and release evidence.

### Optional specialists
- Security engineer.
- Data/ML engineer for future semantic/agent capabilities.
- Product/UX researcher for enterprise client journeys.

## Hosting baseline
### Staging
- Managed PostgreSQL 16 or equivalent.
- Managed Redis 7 or equivalent.
- Neo4j 5.x managed or isolated container.
- Container runtime for API/workers.
- Next.js production runtime.
- CI/CD runner.
- Secret manager.
- Object storage for evidence.
- Centralized logs/metrics.

### Production later
Use managed database services and isolated private networking where possible. Keep PostgreSQL authoritative, Redis non-authoritative, and Neo4j rebuildable.

## Environment separation
`local → CI → staging → production`

Never use production secrets or production evidence in local/demo environments.

## First deployment milestone
The first cloud milestone is **not public production**. It is a private staging environment where engineers can prove migrations, health checks, E2E flows, backups and observability.
