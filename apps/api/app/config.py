from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import hashlib

DEMO_TOKENS={'demo-submitter-key','demo-reviewer-key','demo-steward-key'}

def _hash(v): return hashlib.sha256(v.encode()).hexdigest()
class Settings(BaseSettings):
    database_url: str = 'postgresql+asyncpg://cin:cin@localhost:5432/cin'
    neo4j_uri: str='bolt://localhost:7687'; neo4j_user:str='neo4j'; neo4j_password:str='cinpassword'
    evidence_dir:str='./data/evidence'; cors_origins:str='http://localhost:3000'; redis_url:str='redis://localhost:6379/0'
    app_environment:str='development'; log_level:str='INFO'
    confidence_combined_support_cap:float=0.90; confidence_high_min_group_score:float=0.70; confidence_high_score_threshold:float=0.85
    confidence_high_min_independent_groups:int=2; confidence_high_gate_epsilon:float=0.000001
    auth_api_keys:str=Field('',validation_alias=AliasChoices('CIN_AUTH_API_KEYS','AUTH_API_KEYS'))
    outbox_reconcile_interval_seconds:int=30; processing_timeout_seconds:int=900
    outbox_backoff_base_seconds:int=2; outbox_socket_timeout_seconds:float=1.5
    outreach_cooldown_seconds:int=86400; outreach_reconcile_interval_seconds:int=60
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
    @model_validator(mode='after')
    def validate_security(self):
        validate_auth_policy(self.app_environment, self.auth_api_keys)
        return self
def validate_auth_policy(environment: str, auth_api_keys: str) -> None:
    entries=[x.strip() for x in auth_api_keys.split(',') if x.strip()]
    if environment.lower()=='production':
        if not entries: raise ValueError('CIN_AUTH_API_KEYS must be configured in production')
        demo_hashes={_hash(x) for x in DEMO_TOKENS}
        for entry in entries:
            parts=entry.split(':',2)
            if len(parts)==3 and parts[2].lower() in demo_hashes:
                raise ValueError('Demo API keys are forbidden in production')

settings=Settings()
