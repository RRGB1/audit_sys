# ARCHITECTURE.md

## ארכיטקטורת תוכנה — Enterprise Audit Management MVP

**תאריך:** 19.09.2026  
**סטטוס:** Final Architecture Baseline for MVP  
**מיקום מומלץ בפרויקט:** `docs/ARCHITECTURE.md`

**מסמכי בסיס:**
- `PRODUCT_ANALYSIS.md`
- `TARGET_AUDIENCE.md`
- `DESIGN_SYSTEM.md`
- `SCREENS_FLOW.md`

> מטרת המסמך היא להגדיר ארכיטקטורה ברורה, בדיקה וניתנת להרחבה עבור מערכת ניהול מבדקים ארגונית.  
> הארכיטקטורה צריכה לאפשר להתחיל ב-MVP מקומי ופשוט, לעבור לפיילוט רב-משתמשי על PostgreSQL, ולהוסיף בעתיד SSO, הרשאות מתקדמות, אינטגרציות, Analytics ו-AI — בלי לשכתב את לוגיקת ה-Audit, Finding, Verification, Effectiveness וה-Closure.

---

# 0. מקרא החלטות ומקורות

| סימון | משמעות |
|---|---|
| `[PA]` | נגזר מ-`PRODUCT_ANALYSIS.md` |
| `[TA]` | נגזר מ-`TARGET_AUDIENCE.md` |
| `[DS]` | נגזר מ-`DESIGN_SYSTEM.md` |
| `[SF]` | נגזר מ-`SCREENS_FLOW.md` |
| `[REQUIRED]` | נדרש כדי לשמר את התנהגות המוצר כפי שאופיינה |
| `[PROPOSED]` | החלטת ארכיטקטורה מומלצת שדורשת אישור |
| `[OPEN]` | החלטה שטרם הוכרעה |
| `[CONFIG]` | כלל שלא נכון לקבע בקוד ויש לנהלו בקונפיגורציה |
| `[FUTURE]` | מוכן ארכיטקטונית, אך אינו חלק מה-MVP |

---

# PART A — ARCHITECTURE DRIVERS

# 1. Product-to-Architecture Drivers

| דרייבר מהאפיון | השלכה ארכיטקטונית |
|---|---|
| Audit הוא Lifecycle ולא מסמך סטטי `[PA]` | מעברי מצב מנוהלים ב-Domain/Application, לא ב-UI |
| Audit Closure ו-Finding Closure מבוססי Gate `[SF]` | מקור אמת אחד ל-Closure Rules ב-Policies |
| Verification נפרד מ-Effectiveness `[PA][SF]` | מודלים ושירותים נפרדים, Effectiveness מותנה |
| Root Cause / Effectiveness אינם חובה גלובלית `[SF]` | `PolicyConfig` / Policy ולא `if` קשיח |
| Evidence הוא First-Class Entity `[PA]` | Metadata נפרד מהקובץ ו-Traceability מלאה |
| Audit Trail נדרש לכל שינוי מהותי `[PA]` | Audit Trail נכתב באותה Transaction ב-PostgreSQL |
| הרשאות, סיווג מידע ו-SoD הם Core `[PA]` | Authorization Policy + Storage safeguards + Audit Logging |
| Conflict ללא Silent Overwrite `[SF]` | Optimistic Concurrency עם `version` |
| Dashboard הוא Role-Based `[TA][SF]` | Read Models נפרדים ל-Dashboard |
| Report הוא Snapshot ולא View חי `[PA]` | `ReportVersion` immutable snapshot |
| JSON → PostgreSQL | Ports + Repository Contracts + Migration Tool |
| Cloud / On-Prem / Closed Network עדיין פתוח `[PA][TA]` | אין תלות הכרחית בספק SaaS יחיד |
| Multi-Tenancy עדיין פתוח `[TA]` | Tenant-ready, אך לא Tenant-committed |

---

# 2. Architecture Decisions

| ID | החלטה | סטטוס |
|---|---|---|
| `A1` | **Modular Monolith** ל-MVP | `[PROPOSED]` |
| `A2` | שכבות: **Domain / Application / Storage / Infrastructure / Interfaces** | `[REQUIRED]` |
| `A3` | Domain אינו תלוי ב-FastAPI, SQLAlchemy, Streamlit, JSON או PostgreSQL | `[REQUIRED]` |
| `A4` | Domain Entities בעיקר `@dataclass(slots=True, kw_only=True)` | `[PROPOSED]` |
| `A5` | Value Objects / Domain Events / Snapshots יכולים להיות `frozen=True` | `[PROPOSED]` |
| `A6` | Pydantic משמש בגבולות המערכת | `[PROPOSED]` |
| `A7` | UUID הוא Primary Identifier פנימי; Business Code נפרד | `[REQUIRED]` |
| `A8` | Lifecycle transitions מוגדרים דקלרטיבית | `[PROPOSED]` |
| `A9` | Closure Gate מחזיר `GateResult`, לא Boolean בלבד | `[PROPOSED]` |
| `A10` | JSON הוא Backend מקומי Single-Process בלבד | `[REQUIRED]` |
| `A11` | PostgreSQL הוא יעד ה-Shared Pilot / Production | `[REQUIRED]` |
| `A12` | Neon הוא Deployment option בלבד | `[PROPOSED]` |
| `A13` | Domain Events קיימים מה-MVP; Transactional Outbox נוסף משלב PostgreSQL | `[PROPOSED]` |
| `A14` | Read Models ל-Dashboard — ללא CQRS מלא | `[PROPOSED]` |
| `A15` | Multi-Tenancy Ready, not Committed | `[PROPOSED]` |
| `A16` | Separation of Layers נאכף אוטומטית ב-CI | `[PROPOSED]` |
| `A17` | `uv`, `pytest`, `ruff`, `mypy`, GitHub Actions הם Quality Gates | `[REQUIRED]` |
| `A18` | Idempotency נדרש לפעולות Side-Effect רגישות | `[PROPOSED]` |

---

# 3. Non-Goals for MVP

לא לבנות ב-MVP:

- Microservices.
- Service נפרד לכל Entity.
- Distributed Transactions.
- Message Broker כתלות בסיסית.
- Kubernetes כתנאי לפיתוח.
- Event Sourcing מלא.
- Generic Repository אחד לכל המערכת.
- Multi-Tenancy מלא לפני הכרעת מודל Deployment.
- Workflow Engine כבד לפני שה-Lifecycle הוכח.

---

# PART B — ARCHITECTURE OVERVIEW

# 4. Modular Monolith

```text
One Deployable Application
│
├── Domain
├── Application
├── Storage Adapters
├── Infrastructure Adapters
└── Interfaces
```

יתרונות:

- פיתוח מהיר יותר.
- Debugging פשוט.
- Transaction boundaries ברורים.
- אין Distributed Transactions.
- קל להריץ Local / On-Prem.
- ניתן לחלץ מודול בעתיד רק כשנוצר צורך אמיתי.

---

# 5. Dependency Rule

```mermaid
flowchart TD
    IF[Interfaces\nFastAPI / Web / Streamlit / CLI / Jobs]
    APP[Application\nServices / Policies / Read Models]
    DOM[Domain\nEntities / Enums / Lifecycle / Events]
    PORTS[Ports\nRepositories / UoW / FileStore / Clock / Notifications]
    ST[Storage\nMemory / JSON / PostgreSQL]
    INF[Infrastructure\nIdentity / Notifications / Reports]
    BOOT[Bootstrap / Composition Root]

    IF --> APP
    APP --> DOM
    APP --> PORTS
    ST -. implements .-> PORTS
    INF -. implements .-> PORTS
    ST --> DOM
    INF --> DOM
    BOOT --> IF
    BOOT --> ST
    BOOT --> INF
```

---

# 6. Layer Import Rules

## Domain

מותר:
- Python Standard Library בלבד.

אסור:
- FastAPI
- SQLAlchemy
- psycopg
- Streamlit
- Typer
- Alembic
- Storage adapters
- API DTOs

## Application

מותר:
- Domain
- Ports

אסור:
- Concrete Storage
- ORM Models
- FastAPI
- Streamlit

## Storage / Infrastructure

מממשים Ports שהוגדרו ב-Application.

## Interfaces

מתרגמים Request/Command ל-Application Call.

אסור להם:
- להחליט Business Transition.
- לשכפל Closure Rules.
- לבצע SQL ישירות.

---

# 7. Request Flow

```text
HTTP / CLI / UI
→ Interface
→ DTO / Input Mapping
→ ActorContext
→ Application Service
→ Authorization / Policies
→ UnitOfWork
→ Repositories
→ Domain Entities
→ Audit Trail / Domain Events
→ Commit
→ Result Mapping
→ Response
```

---

# PART C — MODEL LAYER / DOMAIN

# 8. Domain Responsibilities

Domain מגדיר:

- Entities.
- Value Objects.
- Enums.
- Lifecycle states.
- Legal transitions.
- Local invariants.
- Domain Events.
- Domain Errors.

Domain אינו יודע:

- איפה הנתונים נשמרים.
- מי ספק ה-SSO.
- איך נראה UI.
- איך נשלח Email.
- איך SQL נראה.

---

# 9. Dataclass vs Pydantic

## 9.1 Domain Entities

מומלץ:

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(slots=True, kw_only=True)
class Audit:
    title: str
    created_at: datetime
    id: UUID = field(default_factory=uuid4)
    status: "AuditStatus" = AuditStatus.DRAFT
    version: int = 1

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise DomainValidationError("Audit title is required")
        if self.created_at.tzinfo is None:
            raise DomainValidationError("created_at must be timezone-aware")
        if self.version < 1:
            raise DomainValidationError("version must be >= 1")
```

### כלל

Audit / Finding / Action / Evidence:
- `dataclass(slots=True, kw_only=True)`
- שינוי רק דרך Domain/Application operations.

Value Objects / Domain Events / Snapshots:
- `frozen=True` מתאים כברירת מחדל.

---

## 9.2 Pydantic Boundaries

Pydantic משמש ל:

- FastAPI Request / Response.
- Settings.
- JSON input validation.
- CLI input לפי צורך.

```python
class CreateAuditRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    audit_type_id: UUID
```

### אסור

```text
Domain Entity
= API DTO
= ORM Model
= JSON Document
```

---

# 10. Four-Level Validation Model

| רמה | אחריות | דוגמה |
|---|---|---|
| Domain `__post_init__` | Invariants מקומיים | title לא ריק, `version >= 1`, timezone-aware |
| Pydantic | Input / DTO / Settings | format, types, min/max length |
| Service / Policy | כללים חוצי ישויות והרשאות | Audit לא נסגר עם Finding פתוח |
| PostgreSQL Constraints | הגנת נתונים נוספת | FK, UNIQUE, CHECK, NOT NULL |

### כלל

DB Constraint אינו תחליף ל-Business Rule.

---

# 11. Single Source of Truth

| כלל | מקור אמת |
|---|---|
| Status Enums | `domain/enums.py` |
| Legal Transitions | `domain/lifecycle.py` |
| Local Invariants | Entity / Value Object |
| Finding Progress | `domain/progress.py` |
| Closure Rules | `application/policies/closure.py` |
| Authorization Rules | `application/policies/authorization.py` |
| SoD Rules | `application/policies/segregation.py` |
| Effectiveness Requirement | `PolicyConfig` + Effectiveness Policy |
| UI Labels / Colors | Design System / Frontend mapping |

---

# 12. UUID + Business Code

כל Entity ליבה מקבלת UUID פנימי:

```text
Audit.id
Finding.id
Evidence.id
Action.id
User.id
```

בנוסף Business Code:

```text
AUD-2026-0042
FND-2026-0108
```

Business Code:
- מוצג למשתמש.
- אינו Primary Key.
- אינו Foreign Key מרכזי.

---

# 13. Time Strategy

- `datetime` נשמר timezone-aware UTC.
- `date` משמש ליעדים עסקיים.
- המרה לזמן מקומי רק ב-Interfaces.
- Domain לא קורא `datetime.now()` ישירות.

Port:

```python
class Clock(Protocol):
    def now(self) -> datetime: ...
```

---

# 14. Aggregate Boundaries

## Audit Aggregate

```text
Audit
├── programme reference
├── scope
├── team references
├── criteria/checklist references
├── report state
└── lifecycle state
```

## Finding Aggregate

```text
Finding
├── immediate correction
├── root cause
├── corrective actions
├── verification
├── effectiveness checks
├── extensions
└── closure state
```

## Evidence

Evidence נשאר Entity עצמאי וניתן לקשר ל:

- Audit.
- Criterion.
- Checklist Item.
- Finding.
- Corrective Action.
- Verification.
- Effectiveness Check.

---

# 15. Core Domain Entities

```text
AuditProgramme
Audit
AuditType
AuditObject
Standard
Requirement
AuditCriterion
ChecklistTemplate
ChecklistVersion
ChecklistQuestion
AuditChecklistItem
Evidence
Finding
CorrectiveAction
Verification
EffectivenessCheck
DueDateExtension
ReportVersion
User
RoleAssignment
AuditTrailEntry
```

`[FUTURE]`:

```text
AuditorQualification
AuditUniverse
RiskAssessment
IntegrationReference
```

---

# 16. Lifecycle Tables

Legal transitions מוגדרים כנתונים:

```python
AUDIT_TRANSITIONS = {
    AuditStatus.DRAFT: {
        AuditStatus.PLANNED,
        AuditStatus.CANCELLED,
    },
    AuditStatus.PLANNED: {
        AuditStatus.ISSUED,
        AuditStatus.POSTPONED,
        AuditStatus.CANCELLED,
    },
    AuditStatus.ISSUED: {
        AuditStatus.IN_PROGRESS,
        AuditStatus.POSTPONED,
        AuditStatus.CANCELLED,
    },
    AuditStatus.IN_PROGRESS: {
        AuditStatus.COMPLETED,
        AuditStatus.CANCELLED,
    },
    AuditStatus.COMPLETED: {
        AuditStatus.CLOSED,
    },
    AuditStatus.CLOSED: {
        AuditStatus.REOPENED,
    },
}
```

הטבלה קובעת:

> האם מעבר X → Y חוקי בכלל.

Application Policy קובעת:

> האם המשתמש הנוכחי רשאי לבצע את המעבר והאם התנאים התקיימו.

---

# 17. Finding Status Model

מומלץ לשמור Status גס:

```text
OPEN
IN_TREATMENT
PENDING_VERIFICATION
PENDING_EFFECTIVENESS
READY_TO_CLOSE
CLOSED
REOPENED
CANCELLED
```

`WAIVED / ACCEPTED_RISK`:
- `[CONFIG]`
- Disabled by default.
- מופעל רק אם קיים תהליך ארגוני פורמלי שמאפשר זאת.

Correction, RCA ו-Corrective Action הם Data/Sub-entities ולא Status קשיח.

---

# 18. Finding Progress Derivation

פס ההתקדמות ב-UI נגזר מהנתונים.

פונקציה טהורה:

```python
progress(finding, policy)
```

ממפה:

| שלב UI | נגזר מ |
|---|---|
| Open | `status == OPEN` |
| Immediate Correction | correction קיים |
| Root Cause | root cause קיים או אינו נדרש |
| Corrective Action | קיימת לפחות Action אחת |
| Implementation | Actions הושלמו + Evidence |
| Verification | Verification מאושר |
| Effectiveness | Check הושלם או אינו נדרש |
| Closed | `status == CLOSED` |

כך ה-UI נשאר עשיר בלי להפוך את ה-State Machine לקשיחה.

---

# 19. Snapshot & Versioning

כאשר Audit עובר ל-`Issued`:

```text
ChecklistTemplate
→ ChecklistVersion
→ AuditChecklistSnapshot
```

Snapshot שומר:

- question identifier.
- criterion reference.
- organization-owned text.
- evidence rule.
- order.
- response model.

### תוכן תקני

יש לשמור טקסט מלא של תקן רק אם קיימת הרשאת שימוש מתאימה. אחרת שומרים Reference / Clause identifier.

---

# PART D — SERVICES LAYER / APPLICATION

# 20. Application Responsibilities

כל Use Case:

1. מקבל ActorContext + Input.
2. טוען Entities דרך Repository Port.
3. בודק Authorization.
4. מפעיל Policies.
5. משנה Domain State.
6. מייצר Audit Trail.
7. מייצר Domain Event לפי צורך.
8. מבצע Commit.
9. מחזיר Result.

Application אינו:
- מריץ SQL.
- קורא JSON ישירות.
- מחזיר HTML.
- מכיר FastAPI `Request`.

---

# 21. Core Use Cases

```text
CreateAudit
PlanAudit
IssueAudit
StartAudit
CompleteAuditExecution

RecordChecklistResponse
AttachEvidence
OpenFinding

UpdateFindingTreatment
SubmitFindingForVerification
VerifyFinding
RejectFindingEvidence

ScheduleEffectivenessCheck
RecordEffectivenessResult

RequestDueDateExtension
ApproveDueDateExtension

CloseFinding
ReopenFinding

GenerateAuditReport
ApproveAuditReport
CloseAudit
ReopenAudit
```

---

# 22. Policies

```text
AuditTransitionPolicy
FindingTransitionPolicy
FindingClosurePolicy
AuditClosurePolicy
AuthorizationPolicy
SegregationOfDutiesPolicy
EffectivenessRequirementPolicy
ExportPolicy
NotificationContentPolicy
```

Policy היא Single Source of Truth לכלל שחוצה מספר Entities.

---

# 23. GateResult

```python
@dataclass(frozen=True, slots=True)
class Blocker:
    kind: BlockerKind
    ref_type: str | None
    ref_id: UUID | None
    params: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class GateResult:
    passed: bool
    satisfied: tuple[BlockerKind, ...]
    blockers: tuple[Blocker, ...]
```

ה-UI מציג:

```text
✓ הביצוע הסתיים
✓ הדוח אושר
✕ F-014 עדיין פתוח            [פתח]
✕ F-019 ממתין לאפקטיביות     [פתח]
```

בלי לשכפל את ה-Business Rule ב-Frontend.

---

# 24. Ports

```text
AuditRepository
FindingRepository
EvidenceRepository
AuditTrailRepository
DashboardReadPort
UnitOfWork
FileStore
Clock
IdGenerator
BusinessCodeGenerator
NotificationSender
IdentityProvider
ReportRenderer
```

---

# 25. Repository Pattern

```python
class AuditRepository(Protocol):
    def get(self, audit_id: UUID) -> Audit | None: ...
    def add(self, audit: Audit) -> None: ...
    def save(self, audit: Audit, *, expected_version: int) -> None: ...
    def list_for_programme(self, programme_id: UUID) -> Sequence[Audit]: ...
```

לא ליצור:

```python
repository.save(anything)
```

---

# 26. Unit of Work

```python
class UnitOfWork(Protocol):
    audits: AuditRepository
    findings: FindingRepository
    evidence: EvidenceRepository
    audit_trail: AuditTrailRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

PostgreSQL:
- Transaction אמיתי.

JSON:
- Commit אטומי של Snapshot מקומי.

---

# 27. Read Models — Separated Read Side

Dashboard דורש Queries שאינם טבעיים ל-Write Aggregates.

לכן:

```text
DashboardQueryService
    ↓
DashboardReadPort
```

Read Models:

```text
ProgrammeSummary
AuditAttentionItem
FindingOwnerCard
VerificationQueueItem
```

### JSON
חישוב בזיכרון.

### PostgreSQL
Aggregate Queries יעילות.

### לא מדובר ב-CQRS מלא

אין:
- Event Store.
- Database נפרד.
- Async replication.

---

# 28. Domain Events

קטלוג בסיסי:

```text
audit_created
audit_issued
audit_started
audit_completed
audit_closed

finding_created
finding_assigned
finding_submitted
verification_approved
verification_rejected
effectiveness_scheduled
effectiveness_completed
effectiveness_failed
finding_reopened
finding_closed
```

### JSON Stage

```text
commit
→ domain event handling
→ NotificationPort
```

### PostgreSQL Stage

```text
business data + outbox event
→ same transaction
→ worker
```

---

# 29. Actor Context

```python
@dataclass(frozen=True, slots=True)
class ActorContext:
    user_id: UUID
    roles: frozenset[str]
    scopes: frozenset[str]
    clearance: frozenset[str]
```

Tenant Context יתווסף אם Multi-Tenancy יאושר.

---

# 30. Multi-Tenancy Decision Gate

כרגע Multi-Tenancy הוא `[OPEN]`.

## MVP baseline

- Domain אינו מחייב `tenant_id` בכל Entity.
- JSON אינו בנוי לפי Tenant.
- PostgreSQL אינו מחייב RLS לפני החלטת Product/Deployment.

## אם Shared SaaS Multi-Tenant יאושר

ADR נפרד מאשר:

```text
TenantContext
tenant_id columns
Tenant-aware repositories
RLS
Tenant-scoped business codes
Tenant bootstrap
```

החלטה זו צריכה להתקבל לפני Schema Freeze של PostgreSQL.

---

# PART E — STORAGE LAYER

# 31. Storage Adapters

```text
InMemoryRepository
JsonRepository
PostgresRepository
```

אותם Application Services עובדים מול כולם.

---

# 32. Phase 0 — Memory

ל:
- Unit tests.
- Scenario tests.
- Business rule development.

---

# 33. Phase 1 — JSON Prototype

JSON מיועד ל:

- Local development.
- Single-process prototype.
- Demo.
- Early model validation.

אינו מיועד ל:

- Shared pilot.
- Concurrent writers.
- Production authorization.
- RLS.
- High-volume queries.

---

# 34. Simple JSON Snapshot

```text
data/
├── store.json
└── attachments/
```

`store.json`:

```json
{
  "schema_version": 1,
  "store_revision": 17,
  "programmes": {},
  "audits": {},
  "findings": {},
  "evidence": {},
  "users": {},
  "audit_trail": []
}
```

Commit:

```text
load snapshot
→ mutate in memory
→ serialize
→ write temporary file
→ atomic replace
```

### עיקרון

לא לבנות Journal, locking מורכב או pseudo-transactions.

כאשר נדרשת Concurrency אמיתית — עוברים ל-PostgreSQL.

---

# 35. Exit Criteria from JSON

עוברים ל-PostgreSQL כאשר מתקיים אחד:

- יותר מ-Writer אחד במקביל.
- Shared Pilot.
- Transactions אמיתיות.
- Dashboard queries משמעותיים.
- Referential Integrity חזקה.
- Backup/Restore תפעולי.
- Production-grade Audit Trail.
- Data-level authorization מורכב.

---

# 36. Phase 2 — PostgreSQL

Stack מומלץ:

```text
PostgreSQL
SQLAlchemy 2.x
psycopg
Alembic
```

PostgreSQL מספק:

- Transactions.
- Foreign Keys.
- Constraints.
- Indexes.
- Concurrency.
- Optimistic locking.
- Migrations.
- Backup/Recovery.
- Read-side queries.

---

# 37. PostgreSQL Modeling Principles

Relational first.

JSONB מתאים ל:
- flexible metadata.
- Policy configuration.
- integration-specific extension data.

JSONB אינו מחליף:
- Findings.
- Actions.
- Audit relations.
- Permissions.
- Audit Trail.

---

# 38. Conceptual Tables

```text
audit_programmes
audits
audit_team_members
audit_criteria

checklist_templates
checklist_versions
checklist_questions
audit_checklist_items
responses

evidence
attachments

findings
corrective_actions
verifications
effectiveness_checks
due_date_extensions

report_versions

users
roles
permissions
user_role_scopes

audit_trail
```

`[FUTURE]`:

```text
outbox_events
integration_references
risk_assessments
auditor_qualifications
```

---

# 39. Optimistic Concurrency

כל Aggregate הניתן לעריכה מקבל:

```text
version INTEGER
```

Update:

```text
UPDATE ...
WHERE id = :id
  AND version = :expected_version
```

0 rows updated:

```text
VersionMismatchError
→ 409 Conflict
→ UI Conflict State
```

---

# 40. Schema Migrations

Alembic:

```text
model/schema change
→ migration generated
→ migration reviewed
→ committed
→ validated in CI
→ deployed
```

אסור:
- Manual production schema edits.
- Deleting applied migrations.

---

# 41. Repository Contract Tests

אותה Test Suite רצה על:

```text
Memory
JSON
PostgreSQL
```

נבדקים:

- add/get.
- update.
- missing ID.
- duplicate ID.
- round-trip.
- optimistic conflict.
- list/filter semantics.

זהו מנגנון המפתח למעבר JSON → PostgreSQL.

---

# 42. JSON → PostgreSQL Migration

CLI:

```text
audit-cli data migrate-json-to-postgres
```

תהליך:

```text
1. Freeze JSON writes
2. Backup store.json
3. Validate schema_version
4. Validate UUID uniqueness
5. Validate references
6. Transform records
7. Load parent tables
8. Load child tables
9. Load audit trail
10. Verify counts
11. Verify relationships
12. Run contract tests
13. Run Closed Loop scenario
14. Switch STORAGE_BACKEND
15. Smoke test
16. Keep rollback backup
```

Migration Report:

```text
records_read
records_written
records_skipped
invalid_records
broken_references
duplicate_ids
```

---

# 43. PostgreSQL Hosting

Core Architecture מכירה רק:

```text
DATABASE_URL
```

ה-Adapter יכול לעבוד מול:

- Neon.
- Managed PostgreSQL אחר.
- Private Cloud.
- On-Prem PostgreSQL.

פרטי Pooling/TLS/Direct endpoint/Scale-to-zero שייכים ל-`DEPLOYMENT.md`.

---

# PART F — EVIDENCE & FILE STORAGE

# 44. Evidence Metadata vs Binary File

Metadata נשמר ב-Repository.

Binary נשמר ב-FileStore.

```text
Evidence
├── metadata
├── classification
├── content hash
├── storage key
└── domain links
```

אין לשמור Base64 בתוך Entity JSON.

---

# 45. FileStore Port

```python
class FileStore(Protocol):
    def put(self, content: BinaryIO, metadata: FileMetadata) -> StoredFile: ...
    def open(self, file_id: UUID) -> BinaryIO: ...
    def exists(self, file_id: UUID) -> bool: ...
```

Adapters:

```text
LocalFileStore
ObjectStorageFileStore
ControlledEnterpriseFileStore
```

מחיקה פיזית תלויה ב-Retention Policy `[OPEN]`.

---

# PART G — INFRASTRUCTURE

# 46. Infrastructure Adapters

```text
Identity
Notifications
Report Renderers
Clock
External Integration Clients
```

---

# 47. Notifications

## JSON MVP

```text
business commit
→ notification call
```

## PostgreSQL / Shared Pilot

```text
business data + outbox
→ same transaction
→ worker
→ notification
```

---

# 48. Identity

Interfaces/Infrastructure מטפלים ב:

- SSO.
- OIDC/SAML `[OPEN]`.
- MFA `[OPEN]`.
- Session handling.

Application מקבל `ActorContext`.

Services לא רואים Tokens.

---

# 49. Reports

ReportService מפריד בין:

```text
Live Data
```

לבין:

```text
ReportVersion Snapshot
```

בעת Approval:

```text
report_version
generated_at
approved_at
approved_by
source_audit_version
```

Renderers:

```text
PdfReportRenderer
WordReportRenderer
```

---

# PART H — INTERFACES

# 50. FastAPI

Router:

1. Parse Request.
2. Build ActorContext.
3. Call Application Service.
4. Map Error.
5. Map Result to DTO.

Router אינו מכיל Business Rule.

---

# 51. API Structure

```text
/api/v1/
├── programmes
├── audits
├── findings
├── evidence
├── verification
├── effectiveness
├── dashboard
└── reports
```

---

# 52. API DTOs

Pydantic:

```text
CreateAuditRequest
AuditResponse
CreateFindingRequest
FindingResponse
SubmitVerificationRequest
EffectivenessResultRequest
ClosureGateResponse
```

אין להחזיר Domain Entity ישירות.

---

# 53. API Error Mapping

| Error | HTTP | UI |
|---|---|---|
| `NotFoundOrForbidden` | 404 | Not found / unauthorized |
| `PermissionDenied` | 403 | פעולה חסומה |
| `DomainValidationError` | 422 | Validation |
| `InvalidTransitionError` | 409 | Transition Conflict |
| `ClosureBlockedError` | 409 + blockers | Closure Gate |
| `VersionMismatchError` | 409 | Conflict |
| `AuthenticationRequired` | 401 | Re-authentication |

---

# 54. Idempotency

מומלץ עבור פעולות Side-Effect קריטיות:

```text
Submit for Verification
Close Finding
Close Audit
Reopen
```

Interface/API מקבל:

```text
Idempotency-Key
```

Application/Storage מונעים ביצוע כפול.

פרטי המימוש יוגדרו ב-API/Deployment ADR.

---

# 55. Health / Readiness

Endpoints תפעוליים:

```text
GET /health
GET /ready
```

`health`:
- process alive.

`ready`:
- dependencies הנדרשות זמינות.

אין לחשוף מידע רגיש בתגובות.

---

# 56. Dashboard Endpoint

מומלץ:

```text
GET /api/v1/dashboard
```

ולא:

```text
GET /api/v1/dashboard/{role}
```

השרת קובע View לפי `ActorContext`.

---

# 57. Web UI

Production Web:

```text
Web
→ FastAPI
→ Application
```

לא:

```text
Web
→ Database
```

---

# 58. Streamlit

מתאים ל:

- Prototype.
- Demo.
- Internal admin/analysis.

לא מומלץ כ-Production UI הסופי אם נדרשים:

- RTL מדויק.
- Deep Links עשירים.
- Complex tables.
- Figma-level component behavior.

---

# 59. CLI

דוגמאות:

```text
audit-cli seed demo
audit-cli data validate
audit-cli data migrate-json-to-postgres
audit-cli db migrate
audit-cli jobs run reminders
```

---

# 60. Jobs

```text
Reminder Job
Effectiveness Due Job
Outbox Worker
```

Jobs מפעילים Application Services.

---

# PART I — SECURITY ARCHITECTURE

# 61. Authentication

Interface/Infrastructure:

- SSO.
- MFA according to policy.
- Session timeout.
- Identity Provider.

Application מקבל ActorContext בלבד.

---

# 62. Authorization

Policy בודק:

```text
Role
Scope
Object relation
Security Classification
Requested Action
Segregation of Duties
```

RBAC הוא בסיס.

ABAC/Scope מתווספים לפי צורך.

---

# 63. Segregation of Duties

`[CONFIG]`

דוגמה:

```text
Finding Owner may not verify the same Finding
```

הכלל המדויק נקבע במדיניות הארגון.

---

# 64. Data Classification

Domain שומר Classification reference.

Policy קובעת:

- read.
- export.
- download.
- external notification content.

---

# 65. Audit Trail

Audit Trail שומר:

```text
object_type
object_id
action
previous_value
new_value
actor_id
timestamp
reason
correlation_id
```

### PostgreSQL

Business Change ו-Audit Trail באותה Transaction.

### JSON

Audit Trail כחלק מ-Snapshot commit.

---

# 66. Export & File Access

כל Export/Download עובר Authorization.

אין Direct Public URL לראיות רגישות כברירת מחדל.

---

# 67. Sensitive Logging

לוגים תפעוליים לא יכילו כברירת מחדל:

- Finding descriptions.
- Evidence content.
- passwords/tokens.
- sensitive attachments.
- classified text.

לוגים כן יכולים לכלול:

```text
trace_id
user_id
object_id
event type
result
duration
```

לפי מדיניות הארגון.

---

# PART J — DIRECTORY STRUCTURE

# 68. Project Structure

```text
audit-system/
│
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env
├── .env.example
├── .gitignore
├── README.md
├── alembic.ini
│
├── .github/
│   └── workflows/
│       └── ci.yaml
│
├── docs/
│   ├── PRODUCT_ANALYSIS.md
│   ├── TARGET_AUDIENCE.md
│   ├── DESIGN_SYSTEM.md
│   ├── SCREENS_FLOW.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── adr/
│       ├── 0001-modular-monolith.md
│       ├── 0002-domain-models.md
│       ├── 0003-repository-uow.md
│       └── 0004-json-to-postgresql.md
│
├── src/
│   └── audit_system/
│       ├── __init__.py
│       │
│       ├── domain/
│       │   ├── models/
│       │   │   ├── audit.py
│       │   │   ├── programme.py
│       │   │   ├── checklist.py
│       │   │   ├── evidence.py
│       │   │   ├── finding.py
│       │   │   ├── action.py
│       │   │   ├── verification.py
│       │   │   └── user.py
│       │   ├── enums.py
│       │   ├── lifecycle.py
│       │   ├── progress.py
│       │   ├── events.py
│       │   ├── value_objects.py
│       │   └── errors.py
│       │
│       ├── application/
│       │   ├── services/
│       │   ├── policies/
│       │   ├── ports/
│       │   ├── read_models/
│       │   └── commands.py
│       │
│       ├── storage/
│       │   ├── memory/
│       │   ├── json/
│       │   ├── postgres/
│       │   └── files/
│       │
│       ├── infrastructure/
│       │   ├── notifications/
│       │   ├── identity/
│       │   ├── reports/
│       │   └── integrations/
│       │
│       ├── interfaces/
│       │   ├── api/
│       │   ├── web/
│       │   ├── streamlit/
│       │   ├── cli/
│       │   ├── jobs/
│       │   └── i18n/
│       │
│       ├── bootstrap/
│       │   ├── settings.py
│       │   └── container.py
│       │
│       └── observability/
│           ├── logging.py
│           └── correlation.py
│
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── api/
│   ├── migration/
│   ├── scenario/
│   ├── architecture/
│   ├── builders.py
│   ├── fakes.py
│   └── conftest.py
│
├── migrations/
│   ├── env.py
│   └── versions/
│
├── scripts/
│   ├── migrate_json_to_postgres.py
│   ├── seed_demo.py
│   └── validate_data.py
│
└── data/
    └── .gitkeep
```

---

# 69. Composition Root

```python
def build_container(settings: Settings) -> Container:
    if settings.storage_backend == "json":
        uow_factory = JsonUnitOfWorkFactory(...)
    elif settings.storage_backend == "postgres":
        uow_factory = PostgresUnitOfWorkFactory(...)
    else:
        uow_factory = InMemoryUnitOfWorkFactory()

    return Container(
        uow_factory=uow_factory,
        file_store=build_file_store(settings),
        notifier=build_notifier(settings),
        clock=SystemClock(),
    )
```

Services אינם יודעים איזה Adapter נבחר.

---

# PART K — TOOLING & QUALITY

# 70. uv

קבצים:

```text
pyproject.toml
uv.lock
.python-version
.env
.env.example
```

כללים:

- `uv.lock` נכנס ל-Git.
- `.env` לא.
- `.env.example` כן.

---

# 71. pytest Strategy

סוגי בדיקות:

```text
Unit
Contract
Integration
API
Migration
Scenario
Architecture
Negative Security
```

### Unit
Domain + Application ללא DB.

### Contract
אותו Contract לכל Storage Adapter.

### Integration
JSON / PostgreSQL / FileStore / Alembic.

### API
Validation, Status Codes, Error Mapping, Authorization.

### Migration
Schema + JSON → PostgreSQL.

### Scenario
Closed Loop מלא.

### Architecture
Import boundaries.

### Negative Security
Unauthorized actor / SoD / hidden-object behavior.

---

# 72. Coverage

Baseline מוצע:

```text
Global >= 85%
```

אבל Branch tests מפורשים נדרשים עבור:

- Closure.
- Permissions.
- SoD.
- Reopen.
- Effectiveness.
- Invalid transitions.

---

# 73. Ruff

```bash
uv run ruff check .
uv run ruff format --check .
```

---

# 74. Mypy

```bash
uv run mypy src
```

`strict = true` לקוד החדש.

---

# 75. Import Linter

יש לאכוף:

```text
Interfaces / Storage / Infrastructure
            ↓
        Application
            ↓
          Domain
```

הפרה שוברת CI.

---

# 76. Local Quality Command

```bash
uv sync --locked --all-extras --dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run lint-imports
uv run pytest
```

---

# PART L — CI / QUALITY GATES

# 77. CI Principles

PR אינו מתמזג אם אחד נכשל:

- Lock sync.
- Lint.
- Format.
- Type check.
- Architecture boundaries.
- Unit/Contract/Scenario tests.
- PostgreSQL integration when available.
- Negative authorization tests.

---

# 78. `ci.yaml` Baseline

אין לקבע במסמך Architecture גרסאות GitHub Action שמתיישנות במהירות.

ב-Repository בפועל יש לנעוץ Actions ל-Commit SHA מאושר.

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@<PINNED_SHA>

      - name: Install uv
        uses: astral-sh/setup-uv@<PINNED_SHA>
        with:
          enable-cache: true

      - name: Sync
        run: uv sync --locked --all-extras --dev

      - name: Ruff lint
        run: uv run ruff check .

      - name: Ruff format
        run: uv run ruff format --check .

      - name: Mypy
        run: uv run mypy src

      - name: Architecture boundaries
        run: uv run lint-imports

      - name: Pytest
        run: uv run pytest -m "not postgres"

  postgres:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:<APPROVED_VERSION>
        env:
          POSTGRES_USER: audit
          POSTGRES_PASSWORD: audit
          POSTGRES_DB: audit_test
        ports:
          - 5432:5432

    env:
      TEST_DATABASE_URL: postgresql+psycopg://audit:audit@localhost:5432/audit_test

    steps:
      - name: Checkout
        uses: actions/checkout@<PINNED_SHA>

      - name: Install uv
        uses: astral-sh/setup-uv@<PINNED_SHA>

      - name: Sync
        run: uv sync --locked --all-extras --dev

      - name: Migrate
        run: uv run alembic upgrade head

      - name: PostgreSQL tests
        run: uv run pytest -m postgres
```

---

# 79. Pull Request Gates

| Gate | Requirement |
|---|---|
| uv lock | `uv sync --locked` succeeds |
| Ruff | zero lint violations |
| Format | format check passes |
| Mypy | strict passes |
| Architecture | import-linter passes |
| Unit | pass |
| Contract | pass |
| Scenario | Closed Loop passes |
| Coverage | baseline passes |
| PostgreSQL | integration/contract tests pass |
| Security | negative authorization tests pass |

---

# PART M — TESTING STRATEGY

# 80. Test Pyramid

```text
             Scenario / E2E
            Integration
          Contract / API
        Application Unit
         Domain Unit
```

רוב הבדיקות: Unit + Contract.

---

# 81. Test Builders

```python
audit = AuditBuilder().issued().build()
finding = FindingBuilder().pending_verification().build()
```

---

# 82. Blocking Security Tests

חובה לכלול לפחות:

```text
Unauthorized user cannot read restricted object
Finding Owner cannot verify own Finding when SoD requires it
Unauthorized user cannot export restricted evidence
Forbidden object does not reveal sensitive existence/details
```

---

# PART N — IMPLEMENTATION ROADMAP

# 83. M0 — Skeleton + CI

כולל:

- Project structure.
- uv.
- Ruff.
- Mypy.
- Import Linter.
- CI.

Exit:

```text
CI green on skeleton project
```

---

# 84. M1 — Domain + Application

כולל:

- Entities.
- Lifecycle tables.
- Policies.
- Closure Gates.
- Authorization skeleton.
- In-memory repositories.

Exit:

```text
Closed Loop Scenario passes in memory
```

---

# 85. M2 — JSON + CLI

כולל:

- Simple JSON snapshot.
- Contract tests.
- seed/demo.
- data validation.

Exit:

```text
Memory + JSON pass the same contract suite
```

---

# 86. M3 — API + Prototype UI

כולל:

- FastAPI.
- DTOs.
- Error mapping.
- Idempotency foundation.
- Prototype S2/S3/S4.

Exit:

```text
Core flow can be executed through prototype UI
```

---

# 87. M4 — PostgreSQL

כולל:

- SQLAlchemy.
- Alembic.
- PostgreSQL repositories.
- Optimistic concurrency.
- Migration tool.
- PostgreSQL CI job.

Exit:

```text
PostgreSQL passes contracts
JSON migration verified
```

---

# 88. M5 — Enterprise Adapters

כולל:

- SSO.
- Notifications.
- FileStore.
- Transactional Outbox.
- Report renderer.
- Monitoring.

Exit:

```text
Shared pilot ready
```

---

# 89. M6 — Security Hardening

כולל:

- RBAC/ABAC.
- SoD.
- Classification.
- Export/download policy.
- Backup/recovery.
- InfoSec review.

---

# PART O — ADRs

# 90. ADR Baseline

```text
ADR-0001 Modular Monolith
ADR-0002 Domain dataclasses + Pydantic boundaries
ADR-0003 Repository + Unit of Work
ADR-0004 JSON prototype → PostgreSQL
ADR-0005 Evidence file separation
ADR-0006 Optimistic concurrency
ADR-0007 Declarative lifecycle transitions
ADR-0008 GateResult for closure
ADR-0009 Import Linter architecture enforcement
ADR-0010 Streamlit prototype only
ADR-0011 Multi-Tenancy decision gate
ADR-0012 Outbox from PostgreSQL stage
ADR-0013 API idempotency
```

---

# PART P — OPEN DECISIONS

# 91. Open Decisions

1. Python version.
2. Production Web technology.
3. Streamlit future role.
4. SSO protocol/provider.
5. MFA policy.
6. Deployment model.
7. PostgreSQL hosting.
8. File storage platform.
9. Notification channels.
10. RBAC/ABAC matrix.
11. SoD rules.
12. Retention policy.
13. Backup RPO/RTO.
14. Report generation technology.
15. Excel import timing.
16. Root Cause requirement rules.
17. Effectiveness rules.
18. Checklist response model.
19. Security Classification taxonomy.
20. Standards content storage rights.
21. Multi-Tenancy model.
22. Whether RLS is required in the first PostgreSQL pilot.
23. Whether `WAIVED / ACCEPTED_RISK` exists at all.

---

# APPENDIX A — `pyproject.toml` BASELINE

> גרסאות מדויקות ייקבעו בעת הקמת ה-Repository ויינעלו ב-`uv.lock`.

```toml
[project]
name = "audit-system"
version = "0.1.0"
description = "Enterprise Audit Management MVP"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi",
    "pydantic>=2",
    "pydantic-settings",
    "uvicorn[standard]",
]

[project.optional-dependencies]
postgres = [
    "sqlalchemy>=2",
    "psycopg[binary]>=3",
    "alembic",
]
ui = [
    "streamlit",
]

[dependency-groups]
dev = [
    "pytest",
    "pytest-cov",
    "httpx",
    "ruff",
    "mypy",
    "import-linter",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--import-mode=importlib",
    "--strict-config",
    "--strict-markers",
    "--cov=audit_system",
    "--cov-report=term-missing",
    "--cov-fail-under=85",
]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E", "F", "I", "UP", "B", "SIM", "RUF", "DTZ"
]

[tool.mypy]
python_version = "3.12"
mypy_path = "src"
strict = true
warn_unused_configs = true
show_error_codes = true
```

---

# APPENDIX B — JSON → POSTGRESQL MIGRATION CHECKLIST

```text
[ ] Freeze JSON writes
[ ] Backup store.json
[ ] Validate schema_version
[ ] Validate UUID uniqueness
[ ] Validate references
[ ] Validate business codes
[ ] Transform records
[ ] Load parent tables
[ ] Load child tables
[ ] Load audit trail
[ ] Verify row counts
[ ] Verify foreign keys
[ ] Run repository contracts
[ ] Run Closed Loop scenario
[ ] Run API smoke test
[ ] Switch STORAGE_BACKEND
[ ] Keep rollback backup
```

---

# APPENDIX C — ARCHITECTURE DEFINITION OF DONE

הארכיטקטורה נחשבת מיושמת כאשר:

- Domain אינו תלוי ב-Storage/UI/Frameworks.
- Application אינו תלוי ב-Concrete Adapters.
- FastAPI קורא Application Services בלבד.
- JSON Adapter עובר Contract Tests.
- PostgreSQL Adapter עובר אותה Contract Suite.
- Closure Gates נמצאים רק ב-Policies/Services.
- Legal transitions נמצאים במקור אמת אחד.
- Finding progress נגזר מהנתונים ולא מ-State קשיח.
- Evidence metadata מופרד מהקובץ.
- Audit Trail נוצר על Lifecycle transitions.
- Conflict handling מבוסס `version`.
- Idempotency מוגדר לפעולות קריטיות.
- `uv.lock` committed.
- Ruff / Mypy / Pytest / Import Linter עוברים.
- Closed Loop Scenario עובר ב-CI.
- Negative Authorization Tests עוברים.
- JSON → PostgreSQL Migration נבדקה.
- `docs/` מכיל את מסמכי האפיון וה-ADRs.

---

# APPENDIX D — NEXT ARCHITECTURE DOCUMENTS

מומלץ להמשיך עם:

```text
DATA_MODEL.md
API_CONTRACT.md
SECURITY_MODEL.md
DEPLOYMENT.md
MIGRATION_PLAN.md
COMPONENT_SPEC.md
```

`DEPLOYMENT.md` צריך להכיל את הפרטים שהוצאו בכוונה מ-Core Architecture:

- Containers.
- Reverse Proxy.
- TLS termination.
- PostgreSQL sizing.
- Neon pooling/direct endpoint details, אם Neon נבחר.
- Cloud vs On-Prem.
- Backup/PITR.
- Secrets Management.
- Monitoring.
- High Availability.

---

# APPENDIX E — OFFICIAL REFERENCES

המסמך נשען על תכנון המוצר והארכיטקטורה בפרויקט. לצורך אימות Tooling ומימוש בפועל יש להשתמש בתיעוד הרשמי של הפרויקטים בלבד:

- Python: `https://docs.python.org/`
- uv: `https://docs.astral.sh/uv/`
- Ruff: `https://docs.astral.sh/ruff/`
- pytest: `https://docs.pytest.org/`
- Mypy: `https://mypy.readthedocs.io/`
- FastAPI: `https://fastapi.tiangolo.com/`
- Pydantic: `https://docs.pydantic.dev/`
- SQLAlchemy: `https://docs.sqlalchemy.org/`
- Alembic: `https://alembic.sqlalchemy.org/`
- PostgreSQL: `https://www.postgresql.org/docs/`
- GitHub Actions: `https://docs.github.com/actions`
- Import Linter: `https://import-linter.readthedocs.io/`
- Neon, אם ייבחר: `https://neon.com/docs/`

> גרסאות כלים, Actions, Python ו-PostgreSQL חייבות להיבדק בזמן הקמת ה-Repository ולהינעל בפועל בקובצי הפרויקט. אין להסתמך על מספרי גרסאות ארעיים במסמך הארכיטקטורה.

---

# FINAL ARCHITECTURE STATEMENT

```text
Modular Monolith

Domain
  ↑
Application Services + Policies
  ↑
Ports
  ↑
Adapters
  ├── Memory
  ├── JSON Prototype
  ├── PostgreSQL
  ├── File Storage
  ├── Identity
  ├── Notifications
  └── Reports

Interfaces
  ├── FastAPI
  ├── Web
  ├── Streamlit Prototype
  ├── CLI
  └── Jobs
```

העיקרון המרכזי:

> **ה-Domain וה-Business Rules הם המוצר; ה-UI, ה-Database וספקי התשתית הם פרטים ניתנים להחלפה.**

כך המערכת יכולה להתחיל פשוט, להתקדם לפיילוט רב-משתמשי, ולהתרחב בעתיד — בלי לשכתב את הלוגיקה העסקית של Audit, Finding, Verification, Effectiveness ו-Closure.
