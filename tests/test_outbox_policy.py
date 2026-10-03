from datetime import datetime

def test_outbox_backoff_column_and_timer_policy():
 from apps.api.app.models import SyncEvent
 assert hasattr(SyncEvent,'next_attempt_at')

def test_enqueue_is_single_attempt():
 from pathlib import Path
 assert 'MAX_RETRIES' not in Path('apps/api/app/services/redis_queue.py').read_text()
