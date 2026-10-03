"""Bearer API-key authentication with hashed key comparison."""
from dataclasses import dataclass
import hashlib, hmac
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import settings

bearer = HTTPBearer(auto_error=False)

@dataclass(frozen=True)
class Principal:
    subject: str
    role: str

def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def _configured_principals() -> list[tuple[str,str,str]]:
    result=[]
    for item in settings.auth_api_keys.split(','):
        item=item.strip()
        if not item: continue
        try: subject, role, token_hash = item.split(':',2)
        except ValueError: continue
        if role in {'submitter','reviewer','steward'} and len(token_hash)==64:
            result.append((subject,role,token_hash.lower()))
    return result

def current_principal(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> Principal:
    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(401,'AUTHENTICATION_REQUIRED')
    candidate=_hash(credentials.credentials)
    for subject, role, token_hash in _configured_principals():
        if hmac.compare_digest(candidate, token_hash):
            return Principal(subject,role)
    raise HTTPException(401,'INVALID_CREDENTIALS')

def require_roles(*roles: str):
    async def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if principal.role not in roles: raise HTTPException(403,'INSUFFICIENT_ROLE')
        return principal
    return dependency
require_submitter=require_roles('submitter','reviewer','steward')
require_reviewer=require_roles('reviewer','steward')
require_authenticated=require_roles('submitter','reviewer','steward')
require_steward=require_roles('steward')
