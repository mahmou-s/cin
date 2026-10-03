# Security and Production Boundary

## Current controls

- PostgreSQL, Redis and Neo4j are isolated on an internal Docker network.
- Database credentials are environment-injected rather than committed in source.
- API and Worker containers run as a non-root user.
- Alembic is the schema migration authority.
- Evidence is hashed when uploaded by the existing evidence pipeline.
- Verified facts are projected idempotently into Neo4j.
- Failed projections retain retry state and can become `DEAD_LETTER`.
- Redis is authenticated and persisted with AOF.

## Required before unrestricted public production

1. OAuth2/OIDC authentication.
2. Role-based authorization for reviewers and data stewards.
3. Rate limiting and abuse protection at the ingress.
4. TLS termination and HSTS.
5. Secrets manager instead of a long-lived `.env` file.
6. Malware/content scanning for uploaded evidence.
7. Object storage with lifecycle policies for evidence.
8. Structured audit logging and centralized monitoring.
9. Database backups plus tested restore procedures.
10. Dependency and container image vulnerability scanning.

The current release is suitable for a controlled technical demonstration and cloud-hosted MVP; these controls should be completed before open Internet exposure.

## API authentication (current)

The API currently accepts bearer API keys through the `Authorization: Bearer
<TOKEN>` header. Keys are configured with `CIN_AUTH_API_KEYS` as comma-separated
`subject:role:token` entries. Supported roles are `submitter`, `reviewer`, and
`steward`.

Reviewer identity is taken from the authenticated principal and is never read
from the review request body. Only reviewer/steward principals may set evidence
assessments or `independence_key`. A principal cannot review an assertion they
submitted.

This API-key verifier is an authentication boundary designed to be replaced by
JWT/OIDC verification without changing route/service contracts. Never use the
demo keys in a production deployment. The seed script's credential is explicitly
labeled `DEMO STEWARD` and must be replaced in real deployments.

## API authentication hardening
API keys are configured as SHA-256 hashes in `CIN_AUTH_API_KEYS` (`subject:role:sha256`).
The raw key is supplied only to the client/seed environment and is compared with
`hmac.compare_digest`. Production startup rejects empty key sets and rejects the
three documented demo credentials. All write endpoints require authentication;
review endpoints require reviewer/steward and derive the actor from the token.

## Reviewer independence
Submitter-derived URL hosts and file hashes are display-only derived hints. They
are never canonical independence groups until a reviewer explicitly confirms the
hint or supplies an independence key. Otherwise the canonical group is
`__unknown_source__`.
