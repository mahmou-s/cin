import hashlib
import os
import pytest
from apps.api.app.auth import current_principal, Principal
from apps.api.app.config import Settings, validate_auth_policy

def test_api_key_hash_is_sha256_and_hmac_safe():
    from apps.api.app import auth
    raw='unit-secret'; hashed=hashlib.sha256(raw.encode()).hexdigest()
    original=auth.settings.auth_api_keys
    auth.settings.auth_api_keys=f'u:submitter:{hashed}'
    class C: scheme='bearer'; credentials=raw
    assert current_principal(C()) == Principal('u','submitter')
    auth.settings.auth_api_keys=original

def test_production_empty_keys_rejected():
    os.environ.pop('CIN_AUTH_API_KEYS', None)
    with pytest.raises(ValueError, match='CIN_AUTH_API_KEYS'):
        validate_auth_policy('production','')

def test_production_demo_keys_rejected():
    os.environ.pop('CIN_AUTH_API_KEYS', None)
    h=hashlib.sha256(b'demo-reviewer-key').hexdigest()
    with pytest.raises(ValueError, match='Demo API keys'):
        validate_auth_policy('production',f'demo:reviewer:{h}')


def test_missing_token_is_401():
    from apps.api.app.auth import current_principal
    from fastapi import HTTPException
    import asyncio
    with pytest.raises(HTTPException) as exc:
        asyncio.run(current_principal(None))
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_submitter_cannot_review():
    from apps.api.app.auth import require_reviewer, Principal
    from fastapi import HTTPException
    dep=require_reviewer
    with pytest.raises(HTTPException) as exc:
        await dep(Principal('submitter','submitter'))
    assert exc.value.status_code == 403
