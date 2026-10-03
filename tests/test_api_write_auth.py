from pathlib import Path

def test_write_routes_have_auth_dependencies():
 root=Path('apps/api/app/api/v1')
 checks={
  'evidence.py':'require_submitter','graph_reasoning.py':'require_steward','opportunities.py':'require_authenticated',
  'paths.py':'require_authenticated','reasoning.py':'require_authenticated','scenarios.py':'require_authenticated',
  'simulation.py':'require_authenticated','opportunity_review.py':'require_reviewer'
 }
 for fn,dep in checks.items(): assert dep in (root/fn).read_text()

def test_opportunity_review_actor_comes_from_principal():
 s=(Path('apps/api/app/api/v1/opportunity_review.py')).read_text()
 assert 'principal.subject' in s and 'body.actor' not in s
