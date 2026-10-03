from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_production_files_exist():
    required = [
        ROOT / "docker-compose.yml", ROOT / ".env.example", ROOT / "scripts/verify.sh",
        ROOT / "apps/api/alembic.ini", ROOT / "apps/api/migrations/env.py",
        ROOT / "apps/api/migrations/versions/0001_initial_cin.py",
        ROOT / "apps/api/app/services/outbox_worker.py", ROOT / "apps/api/app/services/redis_queue.py",
        ROOT / "seed_civilization.py",
    ]
    assert all(path.exists() for path in required)


def test_source_of_truth_schema_is_transactional_outbox():
    models = (ROOT / "apps/api/app/models.py").read_text()
    migration = (ROOT / "apps/api/migrations/versions/0001_initial_cin.py").read_text()
    assert '__tablename__ = "transactional_outbox"' in models
    assert 'op.create_table("transactional_outbox"' in migration


def test_worker_is_redis_driven_and_reconciles():
    worker = (ROOT / "apps/api/app/services/outbox_worker.py").read_text()
    assert "blpop" in worker
    assert "reconcile_stale_events" in worker
    assert "PROCESSING" in worker
    assert "skip_locked" in worker
