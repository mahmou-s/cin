from apps.api.app.services.confidence import calculate_confidence_details, derive_independence_key

def strong(key):
 return {k:1.0 for k in ['authority','directness','recency','validation','consistency','independence','completeness']} | {'independence_key':key}

def test_distinct_hashless_files_share_unknown_group():
 evidences=[strong('__unknown_source__') for _ in range(10)]
 score, level, raw, reasons=calculate_confidence_details(evidences)
 assert reasons['independent_groups']==1
 assert level!='HIGH'

def test_submitter_host_derivation_is_not_canonical():
 assert derive_independence_key({'content_url':'https://fake-a.example/a'})=='derived-host:fake-a.example'
 score, level, raw, reasons=calculate_confidence_details([strong('__unknown_source__'),strong('__unknown_source__')])
 assert level!='HIGH'
