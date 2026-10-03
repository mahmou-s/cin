from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_release_artifacts_exist():
    required = [
        "docker-compose.yml",
        "seed_civilization.py",
        "SECURITY.md",
        "docs/NVIDIA_TECHNICAL_BRIEF.md",
        "docs/NVIDIA_PRESENTATION_BRIEF.md",
        "docs/ARCHITECTURE_DECISIONS.md",
        "docs/DEMO_SCRIPT.md",
        "docs/PRODUCTION_CHECKLIST.md",
        "apps/api/alembic.ini",
        "apps/api/migrations/versions/0001_initial_cin.py",
        "apps/api/app/services/redis_queue.py",
        "apps/api/app/services/outbox_worker.py",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    assert not missing, missing


def test_architecture_claims_are_conservative():
    brief = (ROOT / "docs/NVIDIA_PRESENTATION_BRIEF.md").read_text()
    assert "CPU-first and GPU-ready" in brief
    assert "does **not** claim" in brief
    assert "measured GPU performance result" in brief


def test_compose_has_migration_queue_and_graph_layers():
    compose = (ROOT / "docker-compose.yml").read_text()
    for service in ["postgres:", "neo4j:", "redis:", "migration:", "api:", "worker:", "web:"]:
        assert service in compose
    assert "alembic" in compose
    assert "REDIS_URL" in compose
    assert "NEO4J_URI" in compose
