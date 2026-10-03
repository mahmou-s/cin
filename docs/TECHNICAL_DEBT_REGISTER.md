# CIN Technical Debt Register

| ID | Priority | Area | Finding | Action | Owner |
|---|---|---|---|---|---|
| TD-001 | P0 | Infrastructure | Real Docker/PostgreSQL/Redis/Neo4j runtime has not been executed in the handoff environment | Establish staging runtime and record evidence | DevOps |
| TD-002 | P0 | Database | 17 sequential migrations need real staging execution with representative existing data | Run upgrade/rollback rehearsal | Backend/DB |
| TD-003 | P0 | Frontend | Production Next.js build/runtime must be executed in CI/staging | Enforce web-build gate | Frontend/DevOps |
| TD-004 | P0 | E2E | Full trust path is not certified end-to-end | Build deterministic E2E scenario | QA/Backend |
| TD-005 | P1 | Security | API-key auth is a demo/MVP boundary, not the final enterprise identity model | Replace/augment with OIDC/OAuth2 + RBAC | Security/Backend |
| TD-006 | P1 | Security | TLS, HSTS, rate limiting, secret manager, malware scanning and vulnerability scanning remain required | Add security baseline | DevOps/Security |
| TD-007 | P1 | Data | Evidence storage currently uses a mounted volume | Move production evidence to object storage with lifecycle/backup | DevOps |
| TD-008 | P1 | Observability | Centralized logs/metrics/traces are not certified | Add OpenTelemetry-compatible observability | DevOps |
| TD-009 | P1 | Resilience | Backup/restore and disaster-recovery drills are not recorded | Run restore rehearsal | DevOps/DB |
| TD-010 | P1 | Architecture | Growing service layer needs explicit ownership boundaries | Freeze core boundaries and document contracts | Architect |
| TD-011 | P2 | Frontend | Web app has many intelligence-specific components | Consolidate shared UI patterns after functional stabilization | Frontend |
| TD-012 | P2 | Product | Research tracks and production features coexist in one repository | Use research/experimental boundaries and feature flags | Product/Architect |
| TD-013 | P2 | Data | Neo4j is a rebuildable projection but rebuild procedure needs an operational runbook | Add projection rebuild and verification command | Backend/DB |
| TD-014 | P2 | Testing | Some tests skip when optional infrastructure packages are absent | CI must install all required test dependencies and fail on skips | QA/DevOps |
