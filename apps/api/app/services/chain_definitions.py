"""Canonical capability-chain definitions shared by all reasoning engines.

Support policy: report both the weakest-link confidence and the arithmetic
average. The weakest-link value is the conservative chain support exposed as
``support_score``; the average is descriptive only and must not be interpreted
as an independent confidence probability.
"""

CHAIN_DEFINITIONS = {
    ("C01", "C10", "C06", "C02"): {
        "label": "Production → External Connectivity → Technology → Market",
        "rationale": "قد تتكامل القدرة الإنتاجية مع الاتصال الخارجي والتكنولوجيا ثم السوق لبناء مسار تطويري قابل للدراسة.",
    },
    ("C01", "C06", "C07", "C03"): {
        "label": "Production → Technology → Innovation → Export",
        "rationale": "تحسين الإنتاج عبر التكنولوجيا ثم الابتكار قد يدعم قابلية التصدير.",
    },
    ("C01", "C02", "C03"): {
        "label": "Production → Market → Export",
        "rationale": "ربط القدرة الإنتاجية بالسوق ثم التصدير قد يفتح مسار وصول إلى أسواق خارجية.",
    },
    ("C01", "C06", "C03", "C10"): {
        "label": "Production → Technology → Export → External Connectivity",
        "rationale": "التكنولوجيا والتصدير قد يتكاملان مع الاتصال الخارجي ضمن مسار محتمل.",
    },
    ("C01", "C02", "C03", "C10"): {
        "label": "Production → Market → Export → External Connectivity",
        "rationale": "السوق والتصدير قد يرتبطان بالاتصال الخارجي ضمن مسار تحليلي محتمل.",
    },
    ("C05", "C07", "C03", "C10"): {
        "label": "Knowledge → Innovation → Export → External Connectivity",
        "rationale": "المعرفة والابتكار قد يدعمان تطوير منتج أو عملية قابلة للتصدير ثم الاتصال الخارجي.",
    },
    ("C04", "C05", "C07"): {
        "label": "Human Capital → Knowledge → Innovation",
        "rationale": "رأس المال البشري والمعرفة قد يدعمان البحث والتطوير والابتكار.",
    },
    ("C08", "C09", "C10"): {
        "label": "Institutional → Cooperation → External Connectivity",
        "rationale": "المؤسسات والتعاون قد يدعمان بناء اتصال خارجي مستمر.",
    },
}

CHAINS = {chain: meta["rationale"] for chain, meta in CHAIN_DEFINITIONS.items()}
PATH_LABELS = {chain: meta["label"] for chain, meta in CHAIN_DEFINITIONS.items()}
PATH_TRANSITIONS = {}
for chain in CHAIN_DEFINITIONS:
    for source, target in zip(chain, chain[1:]):
        PATH_TRANSITIONS.setdefault(source, set()).add(target)


def aggregate_support(scores: list[float]) -> dict[str, float]:
    if not scores:
        return {"weakest_link": 0.0, "average": 0.0}
    values = [float(x) for x in scores]
    return {
        "weakest_link": round(min(values), 4),
        "average": round(sum(values) / len(values), 4),
    }
