"""
Core domain model for the Enterprise Audit Management system.

The module intentionally contains only pure domain objects and business
invariants. It has no dependency on a database, ORM, web framework, API
layer, UI, or external service.

The model is based on PRODUCT_ANALYSIS_V3 and the subsequent review findings.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import ClassVar
from uuid import UUID, uuid4


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def _require_non_empty_text(value: str, field_name: str) -> str:
    """Validate and normalize a mandatory text value."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty.")

    return normalized


def _normalize_optional_text(
    value: str | None,
    field_name: str,
) -> str | None:
    """Validate and normalize an optional text value."""
    if value is None:
        return None

    return _require_non_empty_text(value, field_name)


def _normalize_text(value: str, field_name: str) -> str:
    """Validate a text field that may legitimately be empty."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    return value.strip()


def _normalize_utc_datetime(
    value: datetime | None,
    field_name: str,
) -> datetime | None:
    """
    Validate a datetime and normalize it to UTC.

    Naive datetimes are rejected because the domain model must not guess the
    intended timezone.
    """
    if value is None:
        return None

    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime object.")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")

    return value.astimezone(UTC)


def _validate_uuid4(value: str, field_name: str) -> None:
    """Validate a canonical UUID version 4 string."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a UUID4 string.")
    if not value:
        raise ValueError(f"{field_name} must be a non-empty UUID4 string.")

    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{field_name} '{value}' is not a valid UUID.") from exc

    if parsed.version != 4:
        raise ValueError(f"{field_name} '{value}' must be UUID version 4.")

    if str(parsed) != value:
        raise ValueError(
            f"{field_name} '{value}' must use canonical lowercase UUID format."
        )


class AuditStatus(str, Enum):
    """Lifecycle states of an audit."""

    DRAFT = "draft"
    PLANNED = "planned"
    ISSUED = "issued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"
    REOPENED = "reopened"


class AuditObjectKind(str, Enum):
    """
    Supported categories of auditable objects.

    The values reflect the Audit Object / Auditee categories listed in the
    product analysis. They identify the object category; the actual master
    record is referenced by object_id.
    """

    ORGANIZATIONAL_UNIT = "organizational_unit"
    DEPARTMENT = "department"
    PROCESS = "process"
    SUPPLIER = "supplier"
    PROJECT = "project"
    PRODUCT = "product"
    SITE = "site"
    SYSTEM = "system"


class AuditTeamRole(str, Enum):
    """Role of an auditor inside a specific audit team."""

    LEAD = "lead_auditor"
    AUDITOR = "auditor"


@dataclass(frozen=True, slots=True)
class AuditTypeRef:
    """
    Reference to an Audit Type master-data entity.

    Audit Type is intentionally not implemented as a fixed Enum because the
    product analysis defines it as an entity and leaves the MVP type catalogue
    open for organizational configuration.
    """

    audit_type_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "audit_type_id",
            _require_non_empty_text(self.audit_type_id, "audit_type_id"),
        )


@dataclass(frozen=True, slots=True)
class AuditObjectRef:
    """
    Typed reference to an auditable object.

    This replaces the previous free-text audit_object field and supports an
    audit being linked to one or more Units, Processes, Suppliers, Projects,
    Products, Sites or Systems.
    """

    kind: AuditObjectKind
    object_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AuditObjectKind):
            raise TypeError("kind must be an AuditObjectKind value.")

        object.__setattr__(
            self,
            "object_id",
            _require_non_empty_text(self.object_id, "object_id"),
        )


@dataclass(frozen=True, slots=True)
class AuditTeamMember:
    """
    Auditor assignment inside one audit.

    The Lead Auditor is represented as a team role so the model has one source
    of truth instead of a separate lead_auditor field plus a team collection.
    """

    auditor_id: str
    role: AuditTeamRole = AuditTeamRole.AUDITOR

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "auditor_id",
            _require_non_empty_text(self.auditor_id, "auditor_id"),
        )

        if not isinstance(self.role, AuditTeamRole):
            raise TypeError("role must be an AuditTeamRole value.")


@dataclass(frozen=True, slots=True)
class AuditCriterionSnapshot:
    """
    Immutable snapshot of a criterion used by a specific audit.

    A snapshot prevents historical audits from changing retroactively when a
    Standard, Clause, Procedure, internal instruction, contractual requirement
    or other criterion master record is revised after the audit is issued.

    Attributes:
        criterion_id:
            Stable identifier of the source criterion.
        version:
            Version/revision valid for this audit.
        title:
            Human-readable criterion title.
        requirement_text:
            Requirement content captured for traceability.
        source_type:
            Type/category of requirement source, e.g. standard, procedure,
            customer requirement, internal instruction or contract.
        source_id:
            Identifier of the originating Standard / Procedure / Requirement.
        clause:
            Optional clause/section reference.
    """

    criterion_id: str
    version: str
    title: str
    requirement_text: str
    source_type: str
    source_id: str
    clause: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "criterion_id",
            _require_non_empty_text(self.criterion_id, "criterion_id"),
        )
        object.__setattr__(
            self,
            "version",
            _require_non_empty_text(self.version, "version"),
        )
        object.__setattr__(
            self,
            "title",
            _require_non_empty_text(self.title, "title"),
        )
        object.__setattr__(
            self,
            "requirement_text",
            _require_non_empty_text(
                self.requirement_text,
                "requirement_text",
            ),
        )
        object.__setattr__(
            self,
            "source_type",
            _require_non_empty_text(self.source_type, "source_type"),
        )
        object.__setattr__(
            self,
            "source_id",
            _require_non_empty_text(self.source_id, "source_id"),
        )
        object.__setattr__(
            self,
            "clause",
            _normalize_optional_text(self.clause, "clause"),
        )


@dataclass(frozen=True, slots=True)
class AuditReportRef:
    """Reference to a versioned audit report."""

    report_id: str
    version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "report_id",
            _require_non_empty_text(self.report_id, "report_id"),
        )
        object.__setattr__(
            self,
            "version",
            _require_non_empty_text(self.version, "report version"),
        )


@dataclass(frozen=True, slots=True)
class AuditReportApproval:
    """
    Immutable approval record for the currently attached report version.

    The full report and approval history belong to the Report/Audit Trail
    domains. This value object gives the Audit enough information to enforce
    its local closure invariant.
    """

    report: AuditReportRef
    approved_by: str
    approved_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.report, AuditReportRef):
            raise TypeError("report must be an AuditReportRef.")

        object.__setattr__(
            self,
            "approved_by",
            _require_non_empty_text(self.approved_by, "approved_by"),
        )
        object.__setattr__(
            self,
            "approved_at",
            _normalize_utc_datetime(self.approved_at, "approved_at"),
        )


@dataclass(frozen=True, slots=True)
class AuditClosureGate:
    """
    Closure-gate result calculated from related domain data.

    The Audit aggregate does not own Findings, Actions, Verification or
    Effectiveness Check entities. A Domain/Application service must calculate
    these counts and pass the result to Audit.close().

    All counters must be zero before formal closure.
    """

    open_findings_count: int = 0
    open_actions_count: int = 0
    pending_verifications_count: int = 0
    pending_effectiveness_checks_count: int = 0
    untreated_overdue_items_count: int = 0

    def __post_init__(self) -> None:
        counters = {
            "open_findings_count": self.open_findings_count,
            "open_actions_count": self.open_actions_count,
            "pending_verifications_count": self.pending_verifications_count,
            "pending_effectiveness_checks_count": (
                self.pending_effectiveness_checks_count
            ),
            "untreated_overdue_items_count": self.untreated_overdue_items_count,
        }

        for field_name, value in counters.items():
            if type(value) is not int:
                raise TypeError(f"{field_name} must be an integer.")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative.")

    @property
    def is_clear(self) -> bool:
        """Return True only when all closure-gate counters are zero."""
        return (
            self.open_findings_count == 0
            and self.open_actions_count == 0
            and self.pending_verifications_count == 0
            and self.pending_effectiveness_checks_count == 0
            and self.untreated_overdue_items_count == 0
        )

    def assert_clear(self) -> None:
        """Raise ValueError with detailed blockers when closure is not allowed."""
        blockers: list[str] = []

        if self.open_findings_count:
            blockers.append(
                f"{self.open_findings_count} open finding(s)"
            )
        if self.open_actions_count:
            blockers.append(
                f"{self.open_actions_count} open action(s)"
            )
        if self.pending_verifications_count:
            blockers.append(
                f"{self.pending_verifications_count} pending verification(s)"
            )
        if self.pending_effectiveness_checks_count:
            blockers.append(
                f"{self.pending_effectiveness_checks_count} "
                "pending effectiveness check(s)"
            )
        if self.untreated_overdue_items_count:
            blockers.append(
                f"{self.untreated_overdue_items_count} "
                "untreated overdue item(s)"
            )

        if blockers:
            raise ValueError(
                "Audit cannot be closed because the closure gate is blocked: "
                + ", ".join(blockers)
                + "."
            )


@dataclass(slots=True)
class Audit:
    """
    Aggregate Root / Core Model של ישות המבדק.

    המחלקה מייצגת את ישות הליבה המרכזית במערכת ניהול המבדקים ומנהלת
    את המידע התכנוני ואת מחזור החיים הטהור של המבדק.

    עקרונות המימוש:
    - Pure Domain Model: ללא תלות ב-DB, ORM, API, UI או Framework.
    - מזהה UUID4 וזמן יצירה UTC נוצרים אוטומטית.
    - Audit Type הוא Reference ל-Master Data ולא Enum קשיח.
    - יעד המבדק מיוצג כרשימת AuditObjectRef typed.
    - צוות המבדק משתמש במקור אמת יחיד; Lead Auditor הוא Role בצוות.
    - קריטריונים נשמרים כ-Snapshot versioned לצורך Traceability.
    - כל אוספי הליבה הם tuple כדי למנוע mutation חיצוני.
    - אחרי יצירה, שדות Domain מוגנים משינוי ישיר; שינוי מבוצע רק דרך
      מתודות Domain.
    - לאחר Issued, בסיס התכנון והקריטריונים נעולים.
    - סגירה מתבצעת רק לאחר Report Approval ו-Closure Gate תקין.
    - בדיקות התלויות בישויות חיצוניות מחושבות מחוץ ל-Audit ומוזנות
      אליו כ-AuditClosureGate.

    Important:
        Audit Trail history, authorization, RBAC/ABAC, Segregation of Duties,
        Findings, Actions, Verification and Effectiveness entities are separate
        concerns and are intentionally not embedded into this aggregate.
    """

    title: str
    objective: str = ""
    scope: str = ""

    audit_type: AuditTypeRef | None = None
    audit_programme_id: str | None = None

    audit_objects: tuple[AuditObjectRef, ...] = field(default_factory=tuple)
    team: tuple[AuditTeamMember, ...] = field(default_factory=tuple)
    criteria: tuple[AuditCriterionSnapshot, ...] = field(default_factory=tuple)

    planned_date: datetime | None = None
    security_classification_id: str | None = None

    id: str = field(
        default_factory=lambda: str(uuid4()),
        init=False,
    )
    created_at: datetime = field(
        default_factory=_utc_now,
        init=False,
    )

    status: AuditStatus = field(
        default=AuditStatus.DRAFT,
        init=False,
    )

    started_at: datetime | None = field(default=None, init=False)
    completed_at: datetime | None = field(default=None, init=False)
    closed_at: datetime | None = field(default=None, init=False)

    report: AuditReportRef | None = field(default=None, init=False)
    report_approval: AuditReportApproval | None = field(
        default=None,
        init=False,
    )

    deferred_at: datetime | None = field(default=None, init=False)
    deferred_from_status: AuditStatus | None = field(
        default=None,
        init=False,
    )
    last_defer_reason: str | None = field(default=None, init=False)

    cancelled_at: datetime | None = field(default=None, init=False)
    last_cancel_reason: str | None = field(default=None, init=False)

    reopened_at: datetime | None = field(default=None, init=False)
    last_reopen_reason: str | None = field(default=None, init=False)

    _initialized: bool = field(
        default=False,
        init=False,
        repr=False,
        compare=False,
    )

    _PROTECTED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "title",
            "objective",
            "scope",
            "audit_type",
            "audit_programme_id",
            "audit_objects",
            "team",
            "criteria",
            "planned_date",
            "security_classification_id",
            "id",
            "created_at",
            "status",
            "started_at",
            "completed_at",
            "closed_at",
            "report",
            "report_approval",
            "deferred_at",
            "deferred_from_status",
            "last_defer_reason",
            "cancelled_at",
            "last_cancel_reason",
            "reopened_at",
            "last_reopen_reason",
            "_initialized",
        }
    )

    _BASELINE_EDITABLE_STATES: ClassVar[frozenset[AuditStatus]] = frozenset(
        {
            AuditStatus.DRAFT,
            AuditStatus.PLANNED,
        }
    )

    def __post_init__(self) -> None:
        """
        Normalize and validate the newly created Audit.

        New Audit objects always start in DRAFT. The object becomes mutation-
        controlled after this method: direct assignment to domain fields raises
        AttributeError and changes must go through explicit domain methods.
        """
        object.__setattr__(
            self,
            "title",
            _require_non_empty_text(self.title, "title"),
        )
        object.__setattr__(
            self,
            "objective",
            _normalize_text(self.objective, "objective"),
        )
        object.__setattr__(
            self,
            "scope",
            _normalize_text(self.scope, "scope"),
        )
        object.__setattr__(
            self,
            "audit_programme_id",
            _normalize_optional_text(
                self.audit_programme_id,
                "audit_programme_id",
            ),
        )
        object.__setattr__(
            self,
            "security_classification_id",
            _normalize_optional_text(
                self.security_classification_id,
                "security_classification_id",
            ),
        )

        if self.audit_type is not None and not isinstance(
            self.audit_type,
            AuditTypeRef,
        ):
            raise TypeError("audit_type must be an AuditTypeRef or None.")

        object.__setattr__(
            self,
            "audit_objects",
            tuple(self.audit_objects),
        )
        object.__setattr__(
            self,
            "team",
            tuple(self.team),
        )
        object.__setattr__(
            self,
            "criteria",
            tuple(self.criteria),
        )
        object.__setattr__(
            self,
            "planned_date",
            _normalize_utc_datetime(self.planned_date, "planned_date"),
        )

        self.validate()
        object.__setattr__(self, "_initialized", True)

    def __setattr__(self, name: str, value: object) -> None:
        """
        Block direct mutation after initialization.

        Domain state changes must use the explicit methods on this aggregate so
        invariants are checked atomically.
        """
        if (
            getattr(self, "_initialized", False)
            and name in self._PROTECTED_FIELDS
        ):
            raise AttributeError(
                f"Direct assignment to '{name}' is not allowed. "
                "Use an Audit domain method."
            )

        object.__setattr__(self, name, value)

    @property
    def lead_auditor(self) -> str | None:
        """Return the auditor_id of the single Lead Auditor, if assigned."""
        for member in self.team:
            if member.role == AuditTeamRole.LEAD:
                return member.auditor_id
        return None

    @property
    def report_approved(self) -> bool:
        """Compatibility/readability property for current report approval."""
        return self.report_approval is not None

    @property
    def closure_date(self) -> datetime | None:
        """Compatibility alias for the formal closure timestamp."""
        return self.closed_at

    def validate(self) -> None:
        """
        Validate all local invariants of the Audit aggregate.

        This method can also be used by a repository after rehydration in a
        future persistence layer.
        """
        _validate_uuid4(self.id, "id")

        created_at = _normalize_utc_datetime(self.created_at, "created_at")
        if created_at != self.created_at:
            raise ValueError("created_at must be stored in UTC.")

        if not isinstance(self.status, AuditStatus):
            raise TypeError("status must be an AuditStatus value.")

        _require_non_empty_text(self.title, "title")
        _normalize_text(self.objective, "objective")
        _normalize_text(self.scope, "scope")

        if self.audit_type is not None and not isinstance(
            self.audit_type,
            AuditTypeRef,
        ):
            raise TypeError("audit_type must be an AuditTypeRef or None.")

        _normalize_optional_text(
            self.audit_programme_id,
            "audit_programme_id",
        )
        _normalize_optional_text(
            self.security_classification_id,
            "security_classification_id",
        )

        self._validate_audit_objects()
        self._validate_team()
        self._validate_criteria()
        self._validate_dates()
        self._validate_report()
        self._validate_status_invariants()

    def _validate_audit_objects(self) -> None:
        """Validate auditable-object references and uniqueness."""
        if not isinstance(self.audit_objects, tuple):
            raise TypeError("audit_objects must be a tuple.")

        seen: set[tuple[AuditObjectKind, str]] = set()

        for item in self.audit_objects:
            if not isinstance(item, AuditObjectRef):
                raise TypeError(
                    "Every audit_objects item must be an AuditObjectRef."
                )

            key = (item.kind, item.object_id)
            if key in seen:
                raise ValueError(
                    "audit_objects cannot contain duplicate references."
                )
            seen.add(key)

    def _validate_team(self) -> None:
        """Validate audit team membership and Lead Auditor uniqueness."""
        if not isinstance(self.team, tuple):
            raise TypeError("team must be a tuple.")

        seen_auditors: set[str] = set()
        lead_count = 0

        for member in self.team:
            if not isinstance(member, AuditTeamMember):
                raise TypeError(
                    "Every team item must be an AuditTeamMember."
                )

            if member.auditor_id in seen_auditors:
                raise ValueError(
                    f"Auditor '{member.auditor_id}' appears more than once "
                    "in the audit team."
                )
            seen_auditors.add(member.auditor_id)

            if member.role == AuditTeamRole.LEAD:
                lead_count += 1

        if lead_count > 1:
            raise ValueError(
                "An audit may have only one Lead Auditor."
            )

    def _validate_criteria(self) -> None:
        """Validate criterion snapshots and version uniqueness."""
        if not isinstance(self.criteria, tuple):
            raise TypeError("criteria must be a tuple.")

        seen_criterion_ids: set[str] = set()

        for criterion in self.criteria:
            if not isinstance(criterion, AuditCriterionSnapshot):
                raise TypeError(
                    "Every criteria item must be an "
                    "AuditCriterionSnapshot."
                )

            if criterion.criterion_id in seen_criterion_ids:
                raise ValueError(
                    f"Criterion '{criterion.criterion_id}' appears more "
                    "than once. One audit must reference one frozen version "
                    "of each criterion."
                )

            seen_criterion_ids.add(criterion.criterion_id)

    def _validate_dates(self) -> None:
        """Validate UTC timestamps and chronological ordering."""
        date_fields = {
            "planned_date": self.planned_date,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "closed_at": self.closed_at,
            "deferred_at": self.deferred_at,
            "cancelled_at": self.cancelled_at,
            "reopened_at": self.reopened_at,
        }

        for field_name, value in date_fields.items():
            normalized = _normalize_utc_datetime(value, field_name)
            if value is not None and normalized != value:
                raise ValueError(f"{field_name} must be stored in UTC.")

        if (
            self.started_at is not None
            and self.started_at < self.created_at
        ):
            raise ValueError(
                "started_at cannot be earlier than created_at."
            )

        if (
            self.completed_at is not None
            and self.started_at is None
        ):
            raise ValueError(
                "completed_at requires started_at."
            )

        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError(
                "completed_at cannot be earlier than started_at."
            )

        if self.closed_at is not None and self.completed_at is None:
            raise ValueError(
                "closed_at requires completed_at."
            )

        if (
            self.completed_at is not None
            and self.closed_at is not None
            and self.closed_at < self.completed_at
        ):
            raise ValueError(
                "closed_at cannot be earlier than completed_at."
            )

    def _validate_report(self) -> None:
        """Validate report reference and approval consistency."""
        if self.report is not None and not isinstance(
            self.report,
            AuditReportRef,
        ):
            raise TypeError("report must be an AuditReportRef or None.")

        if self.report_approval is not None:
            if not isinstance(
                self.report_approval,
                AuditReportApproval,
            ):
                raise TypeError(
                    "report_approval must be an AuditReportApproval or None."
                )

            if self.report is None:
                raise ValueError(
                    "A report cannot be approved when no report is attached."
                )

            if self.report_approval.report != self.report:
                raise ValueError(
                    "report_approval must reference the currently attached "
                    "report version."
                )

            if self.report_approval.approved_at < self.created_at:
                raise ValueError(
                    "Report approval cannot be earlier than audit creation."
                )

    def _validate_status_invariants(self) -> None:
        """Validate state-dependent local invariants."""
        statuses_requiring_planning_data = {
            AuditStatus.PLANNED,
            AuditStatus.ISSUED,
            AuditStatus.IN_PROGRESS,
            AuditStatus.COMPLETED,
            AuditStatus.CLOSED,
            AuditStatus.DEFERRED,
            AuditStatus.REOPENED,
        }

        if self.status in statuses_requiring_planning_data:
            missing: list[str] = []

            if self.audit_type is None:
                missing.append("audit_type")
            if not self.audit_objects:
                missing.append("audit_objects")
            if not self.scope:
                missing.append("scope")
            if self.planned_date is None:
                missing.append("planned_date")
            if self.lead_auditor is None:
                missing.append("Lead Auditor")

            if missing:
                raise ValueError(
                    f"Audit in status '{self.status.value}' is missing "
                    f"mandatory planning data: {', '.join(missing)}."
                )

        if self.status == AuditStatus.IN_PROGRESS:
            if self.started_at is None:
                raise ValueError(
                    "IN_PROGRESS audit requires started_at."
                )
            if self.completed_at is not None:
                raise ValueError(
                    "IN_PROGRESS audit cannot have completed_at."
                )
            if self.closed_at is not None:
                raise ValueError(
                    "IN_PROGRESS audit cannot have closed_at."
                )

        if self.status == AuditStatus.COMPLETED:
            if self.started_at is None:
                raise ValueError(
                    "COMPLETED audit requires started_at."
                )
            if self.completed_at is None:
                raise ValueError(
                    "COMPLETED audit requires completed_at."
                )
            if self.closed_at is not None:
                raise ValueError(
                    "COMPLETED audit cannot have closed_at."
                )

        if self.status == AuditStatus.CLOSED:
            if self.started_at is None:
                raise ValueError("CLOSED audit requires started_at.")
            if self.completed_at is None:
                raise ValueError("CLOSED audit requires completed_at.")
            if self.closed_at is None:
                raise ValueError("CLOSED audit requires closed_at.")
            if self.report is None:
                raise ValueError(
                    "CLOSED audit requires an attached report."
                )
            if self.report_approval is None:
                raise ValueError(
                    "CLOSED audit requires report approval."
                )

        if self.status == AuditStatus.DEFERRED:
            if self.deferred_at is None:
                raise ValueError(
                    "DEFERRED audit requires deferred_at."
                )
            if self.deferred_from_status not in {
                AuditStatus.PLANNED,
                AuditStatus.ISSUED,
            }:
                raise ValueError(
                    "DEFERRED audit must originate from PLANNED or ISSUED."
                )
            if not self.last_defer_reason:
                raise ValueError(
                    "DEFERRED audit requires a defer reason."
                )

        if self.status == AuditStatus.CANCELLED:
            if self.cancelled_at is None:
                raise ValueError(
                    "CANCELLED audit requires cancelled_at."
                )
            if not self.last_cancel_reason:
                raise ValueError(
                    "CANCELLED audit requires a cancellation reason."
                )

        if self.status == AuditStatus.REOPENED:
            if self.started_at is None or self.completed_at is None:
                raise ValueError(
                    "REOPENED audit requires the previous execution "
                    "timestamps."
                )
            if self.closed_at is not None:
                raise ValueError(
                    "REOPENED audit must not retain closed_at as the current "
                    "closure timestamp."
                )
            if self.reopened_at is None:
                raise ValueError(
                    "REOPENED audit requires reopened_at."
                )
            if not self.last_reopen_reason:
                raise ValueError(
                    "REOPENED audit requires a reopen reason."
                )

    def _apply_atomic(self, **changes: object) -> None:
        """
        Apply internal state changes atomically.

        If validation fails, every modified field is rolled back before the
        exception is re-raised.
        """
        original = {name: getattr(self, name) for name in changes}

        try:
            for name, value in changes.items():
                object.__setattr__(self, name, value)
            self.validate()
        except Exception:
            for name, value in original.items():
                object.__setattr__(self, name, value)
            raise

    def _ensure_baseline_editable(self) -> None:
        """Reject planning-baseline changes after the audit is issued."""
        if self.status not in self._BASELINE_EDITABLE_STATES:
            raise ValueError(
                "Audit planning baseline is locked after ISSUED. "
                f"Current status is '{self.status.value}'."
            )

    def set_title(self, title: str) -> None:
        """Update audit title while the planning baseline is editable."""
        self._ensure_baseline_editable()
        self._apply_atomic(
            title=_require_non_empty_text(title, "title")
        )

    def set_objective(self, objective: str) -> None:
        """Update audit objective while the planning baseline is editable."""
        self._ensure_baseline_editable()
        self._apply_atomic(
            objective=_normalize_text(objective, "objective")
        )

    def set_scope(self, scope: str) -> None:
        """Update audit scope while the planning baseline is editable."""
        self._ensure_baseline_editable()
        self._apply_atomic(
            scope=_normalize_text(scope, "scope")
        )

    def set_audit_type(self, audit_type: AuditTypeRef) -> None:
        """Assign/change Audit Type before the planning baseline is locked."""
        self._ensure_baseline_editable()

        if not isinstance(audit_type, AuditTypeRef):
            raise TypeError("audit_type must be an AuditTypeRef.")

        self._apply_atomic(audit_type=audit_type)

    def set_audit_programme(self, audit_programme_id: str | None) -> None:
        """
        Assign or clear the Audit Programme reference.

        The product analysis leaves the policy for ad-hoc audits open, so this
        model intentionally keeps programme assignment optional.
        """
        self._ensure_baseline_editable()
        self._apply_atomic(
            audit_programme_id=_normalize_optional_text(
                audit_programme_id,
                "audit_programme_id",
            )
        )

    def set_planned_date(self, planned_date: datetime) -> None:
        """Set the planned audit date/time in UTC."""
        self._ensure_baseline_editable()
        normalized = _normalize_utc_datetime(
            planned_date,
            "planned_date",
        )
        self._apply_atomic(planned_date=normalized)

    def set_security_classification(
        self,
        security_classification_id: str | None,
    ) -> None:
        """
        Set the security-classification master-data reference.

        Classification levels themselves are intentionally external master
        data because the product analysis has not yet fixed the final levels.
        """
        self._ensure_baseline_editable()
        self._apply_atomic(
            security_classification_id=_normalize_optional_text(
                security_classification_id,
                "security_classification_id",
            )
        )

    def replace_audit_objects(
        self,
        audit_objects: Iterable[AuditObjectRef],
    ) -> None:
        """Replace auditable-object references before ISSUED."""
        self._ensure_baseline_editable()
        self._apply_atomic(audit_objects=tuple(audit_objects))

    def replace_team(
        self,
        team: Iterable[AuditTeamMember],
    ) -> None:
        """Replace the audit team before ISSUED."""
        self._ensure_baseline_editable()
        self._apply_atomic(team=tuple(team))

    def replace_criteria(
        self,
        criteria: Iterable[AuditCriterionSnapshot],
    ) -> None:
        """Replace versioned criterion snapshots before ISSUED."""
        self._ensure_baseline_editable()
        self._apply_atomic(criteria=tuple(criteria))

    def plan(self) -> None:
        """
        Move DRAFT → PLANNED.

        Minimum planning data is validated according to the product analysis:
        Audit Type, auditable object, Scope, Planned Date and Lead Auditor.
        """
        if self.status != AuditStatus.DRAFT:
            raise ValueError(
                "Only a DRAFT audit can be moved to PLANNED."
            )

        self._apply_atomic(status=AuditStatus.PLANNED)

    def issue(self) -> None:
        """
        Move PLANNED → ISSUED and lock the planning baseline.

        Any material change after this point belongs to a version/change-log
        workflow outside the simple baseline-edit methods.
        """
        if self.status != AuditStatus.PLANNED:
            raise ValueError(
                "Only a PLANNED audit can be moved to ISSUED."
            )

        self._apply_atomic(status=AuditStatus.ISSUED)

    def start(self, started_at: datetime | None = None) -> None:
        """Move ISSUED → IN_PROGRESS and record the UTC start timestamp."""
        if self.status != AuditStatus.ISSUED:
            raise ValueError(
                "Only an ISSUED audit can be started."
            )

        timestamp = _normalize_utc_datetime(
            started_at or _utc_now(),
            "started_at",
        )
        self._apply_atomic(
            started_at=timestamp,
            completed_at=None,
            closed_at=None,
            status=AuditStatus.IN_PROGRESS,
        )

    def complete(self, completed_at: datetime | None = None) -> None:
        """Move IN_PROGRESS → COMPLETED and record completion timestamp."""
        if self.status != AuditStatus.IN_PROGRESS:
            raise ValueError(
                "Only an IN_PROGRESS audit can be completed."
            )

        timestamp = _normalize_utc_datetime(
            completed_at or _utc_now(),
            "completed_at",
        )

        self._apply_atomic(
            completed_at=timestamp,
            status=AuditStatus.COMPLETED,
        )

    def attach_report(self, report: AuditReportRef) -> None:
        """
        Attach a specific report version.

        Replacing the report automatically invalidates the prior approval
        because approval belongs to an exact report version.
        """
        if self.status not in {
            AuditStatus.IN_PROGRESS,
            AuditStatus.COMPLETED,
            AuditStatus.REOPENED,
        }:
            raise ValueError(
                "A report may be attached only while an audit is "
                "IN_PROGRESS, COMPLETED or REOPENED."
            )

        if not isinstance(report, AuditReportRef):
            raise TypeError("report must be an AuditReportRef.")

        self._apply_atomic(
            report=report,
            report_approval=None,
        )

    def approve_report(
        self,
        approved_by: str,
        approved_at: datetime | None = None,
    ) -> None:
        """
        Approve the currently attached report version.

        Authorization and Segregation of Duties are enforced by the
        Application/Authorization layer; this aggregate records the approved
        report version, approver identity and approval time.
        """
        if self.status != AuditStatus.COMPLETED:
            raise ValueError(
                "Report approval is allowed only for a COMPLETED audit."
            )

        if self.report is None:
            raise ValueError(
                "Cannot approve a report because no report is attached."
            )

        approval = AuditReportApproval(
            report=self.report,
            approved_by=approved_by,
            approved_at=approved_at or _utc_now(),
        )
        self._apply_atomic(report_approval=approval)

    def close(
        self,
        closure_gate: AuditClosureGate,
        closed_at: datetime | None = None,
    ) -> None:
        """
        Formally close a COMPLETED audit.

        Local preconditions:
        - current status is COMPLETED;
        - current report exists and is approved;
        - closure gate reports no open Findings/Actions, no pending
          Verification/Effectiveness checks and no untreated overdue items.

        Authorization and Audit Trail recording are handled outside this pure
        domain model.
        """
        if self.status != AuditStatus.COMPLETED:
            raise ValueError(
                "Only a COMPLETED audit can be CLOSED."
            )

        if not isinstance(closure_gate, AuditClosureGate):
            raise TypeError(
                "closure_gate must be an AuditClosureGate."
            )

        closure_gate.assert_clear()

        if self.report is None:
            raise ValueError(
                "Audit cannot be closed without an attached report."
            )

        if self.report_approval is None:
            raise ValueError(
                "Audit cannot be closed before the report is approved."
            )

        timestamp = _normalize_utc_datetime(
            closed_at or _utc_now(),
            "closed_at",
        )
        assert timestamp is not None

        if self.report_approval.approved_at > timestamp:
            raise ValueError(
                "closed_at cannot be earlier than report approval."
            )

        self._apply_atomic(
            closed_at=timestamp,
            status=AuditStatus.CLOSED,
        )

    def reopen(
        self,
        reason: str,
        reopened_at: datetime | None = None,
    ) -> None:
        """
        Move CLOSED → REOPENED.

        Reopening requires a reason. The current closure timestamp and current
        report approval are cleared; historical closure/approval events are
        expected to remain preserved in the Audit Trail / Report history.
        """
        if self.status != AuditStatus.CLOSED:
            raise ValueError(
                "Only a CLOSED audit can be reopened."
            )

        normalized_reason = _require_non_empty_text(
            reason,
            "reopen reason",
        )
        timestamp = _normalize_utc_datetime(
            reopened_at or _utc_now(),
            "reopened_at",
        )
        assert timestamp is not None

        if self.closed_at is not None and timestamp < self.closed_at:
            raise ValueError(
                "reopened_at cannot be earlier than the previous closed_at."
            )

        self._apply_atomic(
            status=AuditStatus.REOPENED,
            reopened_at=timestamp,
            last_reopen_reason=normalized_reason,
            closed_at=None,
            report_approval=None,
        )

    def resume_reopened(
        self,
        target_status: AuditStatus,
    ) -> None:
        """
        Resume a REOPENED audit as IN_PROGRESS or COMPLETED.

        The product analysis explicitly allows a reopened audit to return to
        Completed or In Progress according to the work required.
        """
        if self.status != AuditStatus.REOPENED:
            raise ValueError(
                "Only a REOPENED audit can be resumed."
            )

        if target_status not in {
            AuditStatus.IN_PROGRESS,
            AuditStatus.COMPLETED,
        }:
            raise ValueError(
                "A REOPENED audit may resume only as IN_PROGRESS "
                "or COMPLETED."
            )

        if target_status == AuditStatus.IN_PROGRESS:
            self._apply_atomic(
                completed_at=None,
                status=AuditStatus.IN_PROGRESS,
            )
            return

        self._apply_atomic(status=AuditStatus.COMPLETED)

    def defer(
        self,
        reason: str,
        deferred_at: datetime | None = None,
    ) -> None:
        """
        Defer a PLANNED or ISSUED audit.

        The exact enterprise policy for Deferred transitions is not fully
        defined in the product analysis. This model uses the conservative MVP
        interpretation that a scheduled audit may be deferred before execution.
        """
        if self.status not in {
            AuditStatus.PLANNED,
            AuditStatus.ISSUED,
        }:
            raise ValueError(
                "Only a PLANNED or ISSUED audit can be DEFERRED."
            )

        normalized_reason = _require_non_empty_text(
            reason,
            "defer reason",
        )
        timestamp = _normalize_utc_datetime(
            deferred_at or _utc_now(),
            "deferred_at",
        )

        previous_status = self.status
        self._apply_atomic(
            status=AuditStatus.DEFERRED,
            deferred_at=timestamp,
            deferred_from_status=previous_status,
            last_defer_reason=normalized_reason,
        )

    def resume_deferred(self) -> None:
        """
        Return a DEFERRED audit to the state from which it was deferred.

        The previous state is retained explicitly to avoid guessing whether the
        audit should resume as PLANNED or ISSUED.
        """
        if self.status != AuditStatus.DEFERRED:
            raise ValueError(
                "Only a DEFERRED audit can be resumed."
            )

        if self.deferred_from_status not in {
            AuditStatus.PLANNED,
            AuditStatus.ISSUED,
        }:
            raise ValueError(
                "Deferred audit has no valid previous lifecycle state."
            )

        target = self.deferred_from_status
        self._apply_atomic(
            status=target,
            deferred_at=None,
            deferred_from_status=None,
        )

    def cancel(
        self,
        reason: str,
        cancelled_at: datetime | None = None,
    ) -> None:
        """
        Cancel an audit that has not already reached CLOSED/CANCELLED.

        The product analysis requires a Cancelled state but does not yet define
        the final transition matrix. Therefore this method applies a minimal
        safe rule: CLOSED and already-CANCELLED audits cannot be cancelled.
        """
        if self.status in {
            AuditStatus.CLOSED,
            AuditStatus.CANCELLED,
        }:
            raise ValueError(
                f"Audit in status '{self.status.value}' cannot be cancelled."
            )

        normalized_reason = _require_non_empty_text(
            reason,
            "cancellation reason",
        )
        timestamp = _normalize_utc_datetime(
            cancelled_at or _utc_now(),
            "cancelled_at",
        )

        self._apply_atomic(
            status=AuditStatus.CANCELLED,
            cancelled_at=timestamp,
            last_cancel_reason=normalized_reason,
        )


# Backward-compatible alias for code that still imports CoreModel from
# src.models.core. New code should use the business/domain name `Audit`.
CoreModel = Audit
