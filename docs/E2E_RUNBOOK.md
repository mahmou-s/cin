# CIN v2.0 — E2E Runbook (Simplified)

## الهدف
تشغيل المنصة كاملة محلياً (Postgres + Redis + Neo4j + API + Workers + Web)، زرع بيانات تجريبية، والتحقق السريع من الصحة — مع إبقاء الخدمات تعمل بعد السكربت.

## المتطلبات
- Docker + Docker Compose v2
- منافذ حرة: `8000` (API)، `3000` (Web)، وداخلياً 5432 / 6379 / 7474 / 7687

## التشغيل السريع

```bash
cd CIN-v2.0-NVIDIA-Technical-Demonstrator-ADR012-PROACTIVE-OUTREACH-V1

# 1) تشغيل كامل + seed + smoke checks (يبقي الخدمات تعمل)
chmod +x scripts/e2e_up.sh scripts/e2e_down.sh
./scripts/e2e_up.sh

# 2) افتح الواجهة
#    Web:  http://localhost:3000
#    API:  http://localhost:8000/health/ready
#    Neo4j Browser: http://localhost:7474  (user: neo4j / password from .env)

# 3) إيقاف
./scripts/e2e_down.sh
```

## ماذا يفعل `e2e_up.sh`؟

1. يُنشئ ملف `.env` محلي بقيم demo إن لم يكن موجوداً.
2. يشغّل postgres / redis / neo4j وينتظر health.
3. يشغّل Alembic `upgrade head`.
4. يشغّل api + worker + outreach_worker + web.
5. ينتظر `/health/ready` (Postgres + Redis + Neo4j).
6. يشغّل `seed_civilization.py`.
7. يفحص smoke: `/health`، `/health/ready`، الواجهة، وعدد عقد CapabilityAssertion في Neo4j.
8. **لا يوقف الخدمات** (عكس `scripts/verify.sh`).

## مفاتيح الـ Demo (محلية فقط)

| الدور | المتغير | القيمة الافتراضية |
|--------|---------|-------------------|
| submitter | `CIN_DEMO_SUBMITTER_API_KEY` | `demo-submitter-key` |
| reviewer | `CIN_DEMO_REVIEWER_API_KEY` | `demo-reviewer-key` |
| steward | `CIN_DEMO_STEWARD_API_KEY` | `demo-steward-key` |

في الواجهة: ضع مفتاح الـ reviewer في Token Settings قبل استخدام مركز التحقق.

**تحذير:** هذه المفاتيح وكلمات المرور للتجربة المحلية فقط. لا تستخدمها في أي بيئة عامة.

## مسار الثقة المتوقع بعد الـ seed

```
Seed assertions → Human review (مراجع) → Verified fact → Outbox → Worker → Neo4j
→ Opportunity paths في الواجهة
```

## استكشاف الأخطاء

| العرض | ماذا تفعل |
|--------|-----------|
| API not ready | `docker compose logs api --tail=100` |
| Migration فشل | تأكد أن postgres healthy ثم أعد `docker compose run --rm migration alembic upgrade head` |
| Seed فشل | تحقق من مفاتيح الـ demo ومن أن API يستجيب على `/health/ready` |
| Web لا يفتح | `docker compose logs web --tail=50` — قد يحتاج وقتاً إضافياً بعد البناء |
| Neo4j count = 0 | انتظر 30–60 ثانية (worker يعالج الـ outbox) ثم أعد الاستعلام |

## الفرق بين السكربتات

| السكربت | الغرض | يوقف الخدمات؟ |
|---------|--------|----------------|
| `scripts/e2e_up.sh` | تشغيل يومي / عرض / تطوير | لا |
| `scripts/e2e_down.sh` | إيقاف نظيف | نعم (volumes تبقى) |
| `scripts/verify.sh` | تحقق CI-style كامل + pytest | نعم (عند الخروج) |

## بعد نجاح E2E — الخطوة التالية الموصى بها

حسب `docs/PRODUCTION_CHECKLIST.md` و `docs/PRODUCT_FOCUS.md`:

1. مسار ثقة يدوي في الواجهة (تقديم → مراجعة → ظهور فرصة).
2. تجربة Proactive Outreach: signal صريح → digest → تحقق قناة.
3. اختيار منطقة + قطاع واحد لبيانات pilot حقيقية.
