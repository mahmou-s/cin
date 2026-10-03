#!/usr/bin/env python3
"""Seed the first demonstrator scenario through the public CIN API.

The script intentionally uses the same API pipeline as a real submission:
1) submit assertion + evidence
2) human-review endpoint verifies the assertion
3) verified event is written to the PostgreSQL transactional outbox
4) API publishes the event ID to Redis
5) Worker projects it into Neo4j
6) opportunity discovery reads VERIFIED assertions only
"""
import argparse
import sys
import time
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEFAULT_API = "http://localhost:8000/api/v1"


DEMO_STEWARD_LABEL = "DEMO STEWARD — replace before production"
DEMO_SUBMITTER_TOKEN = os.getenv("CIN_DEMO_SUBMITTER_API_KEY", "demo-submitter-key")
DEMO_REVIEWER_TOKEN = os.getenv("CIN_DEMO_REVIEWER_API_KEY", "demo-reviewer-key")
DEMO_STEWARD_TOKEN = os.getenv("CIN_DEMO_STEWARD_API_KEY", "demo-steward-key")

def http_json(method, url, payload=None, token=DEFAULT_STEWARD_TOKEN):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"API connection error: {exc}") from exc


def get_capability_ids(api_url):
    return {item["code"]: item["id"] for item in http_json("GET", f"{api_url}/capabilities") }


def submit_and_verify(api_url, capability_id, community, scope, evidences, submitter_token=DEMO_SUBMITTER_TOKEN, reviewer_token=DEMO_REVIEWER_TOKEN):
    payload = {
        "community": community,
        "capability_type_id": capability_id,
        "scope": scope,
        "scale": "demonstration-seed",
        "maturity_level": "ESTABLISHED",
        "evidence": evidences,
    }
    assertion = http_json("POST", f"{api_url}/assertions/submit", payload, submitter_token)

    assessments = []
    for evidence_id, evidence in zip(assertion["evidence_ids"], evidences):
        assessments.append({
            "evidence_id": evidence_id,
            "authority": evidence.get("authority", 0.5),
            "directness": evidence.get("directness", 0.5),
            "recency": evidence.get("recency", 0.5),
            "validation": evidence.get("validation", 0.5),
            "consistency": evidence.get("consistency", 0.5),
            "independence": evidence.get("independence", 0.5),
            "completeness": evidence.get("completeness", 0.5),
            "independence_key": None,
            "confirm_derived_independence": True,
        })
    review = {
        "decision": "VERIFY",
        "note": f"{DEMO_STEWARD_LABEL}. Reviewer values are DEMO values intentionally set by the reviewer token; they are not copied from submitter claims. Revalidation is required before authoritative research use.",
        "contradiction_score": 0.0,
        "evidence_assessments": assessments,
    }
    return http_json("POST", f"{api_url}/assertions/{assertion['id']}/review", review, reviewer_token)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=DEFAULT_API, help="CIN API base URL")
    parser.add_argument("--wait", type=int, default=10, help="seconds to wait before discovery")
    args = parser.parse_args()
    api_url = args.api.rstrip("/")

    try:
        caps = get_capability_ids(api_url)
        required = {"C01", "C02", "C06", "C10"}
        missing = required - caps.keys()
        if missing:
            raise RuntimeError(f"Missing capability codes: {sorted(missing)}")

        seed_rows = [
            ("C01", {"name": "المجتمع A — مصر", "country_code": "EG", "location": "Egypt", "description": "DEMO SEED: agricultural production capability."}, "Agricultural production", [
                {"title": "Government agricultural production evidence — DEMO SEED", "evidence_type": "government_document", "content_text": "DEMO SEED: CAPMAS agricultural indicators.", "content_url": "https://old.capmas.gov.eg/Pages/IndicatorsPage.aspx?Ind_id=2338", "authority": 1.0, "directness": 1.0, "recency": 1.0, "validation": 1.0, "consistency": 1.0, "independence": 1.0, "completeness": 1.0},
                {"title": "Secondary agricultural source — DEMO SEED", "evidence_type": "secondary_source", "content_text": "DEMO SEED: independent secondary source.", "content_url": "https://www.fao.org/faostat/en/", "authority": 0.9, "directness": 0.9, "recency": 0.9, "validation": 0.9, "consistency": 0.9, "independence": 0.9, "completeness": 0.9},
            ]),
            ("C10", {"name": "المجتمع A — مصر", "country_code": "EG", "location": "Egypt", "description": "DEMO SEED: external logistics/connectivity capability."}, "Logistics and external connectivity", [
                {"title": "Government logistics evidence — DEMO SEED", "evidence_type": "government_document", "content_text": "DEMO SEED: Egyptian logistics connectivity source.", "content_url": "https://www.mped.gov.eg/singlenews?id=6166&lang=en", "authority": 1.0, "directness": 1.0, "recency": 1.0, "validation": 1.0, "consistency": 1.0, "independence": 1.0, "completeness": 1.0},
                {"title": "Secondary logistics source — DEMO SEED", "evidence_type": "secondary_source", "content_text": "DEMO SEED: independent secondary source.", "content_url": "https://www.worldbank.org/ext/en/topic/transport", "authority": 0.9, "directness": 0.9, "recency": 0.9, "validation": 0.9, "consistency": 0.9, "independence": 0.9, "completeness": 0.9},
            ]),
            ("C06", {"name": "المجتمع B — منطقة تقنية", "country_code": "XX", "location": "Technology Region", "description": "DEMO SEED: software and agricultural technology capability."}, "Software and agricultural technology", [
                {"title": "Academic technology evidence — DEMO SEED", "evidence_type": "academic_research", "content_text": "DEMO SEED: research on software and precision agriculture technology.", "content_url": "https://www.sciencedirect.com/science/article/pii/S2772375525005763", "authority": 0.95, "directness": 0.95, "recency": 1.0, "validation": 1.0, "consistency": 1.0, "independence": 1.0, "completeness": 1.0},
                {"title": "Secondary technology source — DEMO SEED", "evidence_type": "secondary_source", "content_text": "DEMO SEED: independent secondary source.", "content_url": "https://www.fao.org/digital-village-initiative/en", "authority": 0.9, "directness": 0.9, "recency": 0.9, "validation": 0.9, "consistency": 0.9, "independence": 0.9, "completeness": 0.9},
            ]),
            ("C02", {"name": "المجتمع C — مركز مالي وسوقي", "country_code": "XX", "location": "Financial & Market Center", "description": "DEMO SEED: financial and market capability."}, "Financing and capital deployment", [
                {"title": "World Bank capital markets evidence — DEMO SEED", "evidence_type": "institutional_report", "content_text": "DEMO SEED: World Bank capital markets source.", "content_url": "https://www.worldbank.org/ext/en/topic/financial-sector/capital-markets", "authority": 0.95, "directness": 0.95, "recency": 1.0, "validation": 1.0, "consistency": 1.0, "independence": 1.0, "completeness": 1.0},
                {"title": "Secondary financial source — DEMO SEED", "evidence_type": "secondary_source", "content_text": "DEMO SEED: independent secondary source.", "content_url": "https://www.imf.org/en/Topics/Financial-Systems", "authority": 0.9, "directness": 0.9, "recency": 0.9, "validation": 0.9, "consistency": 0.9, "independence": 0.9, "completeness": 0.9},
            ]),
        ]

        results = []
        for code, community, scope, evidence in seed_rows:
            result = submit_and_verify(api_url, caps[code], community, scope, evidence)
            results.append(result)
            print(f"VERIFIED {code}: assertion={result['id']} confidence={result['confidence_level']} score={result['confidence_score']:.3f}")

        print(f"Waiting {args.wait}s for Redis → Worker → Neo4j projection...")
        time.sleep(args.wait)

        opportunities = http_json("GET", f"{api_url}/civilizational-opportunities/discover?limit=20")
        print(f"Opportunity paths discovered: {len(opportunities)}")
        for opportunity in opportunities[:5]:
            print("-", opportunity["title"])
            print("  chain:", " → ".join(opportunity["capability_chain"]))
            print("  support:", opportunity["support"])

    except RuntimeError as exc:
        print(f"API error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Seed error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
