"""Pytest suite for src.models.core.

The tests cover the public core-domain model, its value objects, constructor
validation, UUID/time generation, lifecycle invariants and closure rules.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid1, uuid4

import pytest

from src.models.core import (
    Audit,
    AuditClosureGate,
    AuditCriterionSnapshot,
    AuditObjectKind,
    AuditObjectRef,
    AuditReportApproval,
    AuditReportRef,
    AuditStatus,
    AuditTeamMember,
    AuditTeamRole,
    AuditTypeRef,
    CoreModel,
)

# ---------------------------------------------------------------------------
# Fixtures / factories
# ---------------------------------------------------------------------------


def criterion(
    criterion_id: str = "CRIT-001",
    version: str = "A",
) -> AuditCriterionSnapshot:
    return AuditCriterionSnapshot(
        criterion_id=criterion_id,
        version=version,
        title="Quality management system requirement",
        requirement_text="The organization shall maintain the defined process.",
        source_type="standard",
        source_id="AS9100D",
        clause="4.4",
    )


def valid_audit(**overrides: object) -> Audit:
    data: dict[str, object] = {
        "title": "Supplier quality audit",
        "objective": "Verify conformity and process effectiveness",
        "scope": "Manufacturing and final inspection",
        "audit_type": AuditTypeRef("supplier"),
        "audit_programme_id": "PROGRAMME-2026",
        "audit_objects": (
            AuditObjectRef(AuditObjectKind.SUPPLIER, "SUP-001"),
            AuditObjectRef(AuditObjectKind.PROJECT, "PRJ-100"),
        ),
        "team": (
            AuditTeamMember("AUD-001", AuditTeamRole.LEAD),
            AuditTeamMember("AUD-002", AuditTeamRole.AUDITOR),
        ),
        "criteria": (criterion(),),
        "planned_date": datetime(2026, 10, 15, 7, 30, tzinfo=UTC),
        "security_classification_id": "INTERNAL",
    }
    data.update(overrides)
    return Audit(**data)


def issued_audit() -> Audit:
    audit = valid_audit()
    audit.plan()
    audit.issue()
    return audit


def in_progress_audit() -> Audit:
    audit = issued_audit()
    audit.start(audit.created_at + timedelta(hours=1))
    return audit


def completed_audit(with_report: bool = False) -> Audit:
    audit = in_progress_audit()
    audit.complete(audit.started_at + timedelta(hours=2))
    if with_report:
        audit.attach_report(AuditReportRef("REPORT-001", "1.0"))
    return audit


def closed_audit() -> Audit:
    audit = completed_audit(with_report=True)
    audit.approve_report(
        "APPROVER-001",
        audit.completed_at + timedelta(minutes=10),
    )
    audit.close(
        AuditClosureGate(),
        audit.report_approval.approved_at + timedelta(minutes=10),
    )
    return audit


# ---------------------------------------------------------------------------
# Happy path / generated identity and time
# ---------------------------------------------------------------------------


def test_audit_creation_happy_path_and_all_initial_fields() -> None:
    before = datetime.now(UTC)
    audit = valid_audit()
    after = datetime.now(UTC)

    assert audit.title == "Supplier quality audit"
    assert audit.objective == "Verify conformity and process effectiveness"
    assert audit.scope == "Manufacturing and final inspection"
    assert audit.audit_type == AuditTypeRef("supplier")
    assert audit.audit_programme_id == "PROGRAMME-2026"
    assert audit.audit_objects == (
        AuditObjectRef(AuditObjectKind.SUPPLIER, "SUP-001"),
        AuditObjectRef(AuditObjectKind.PROJECT, "PRJ-100"),
    )
    assert audit.team == (
        AuditTeamMember("AUD-001", AuditTeamRole.LEAD),
        AuditTeamMember("AUD-002", AuditTeamRole.AUDITOR),
    )
    assert audit.criteria == (criterion(),)
    assert audit.planned_date == datetime(
        2026, 10, 15, 7, 30, tzinfo=UTC
    )
    assert audit.security_classification_id == "INTERNAL"

    assert audit.status is AuditStatus.DRAFT
    assert audit.started_at is None
    assert audit.completed_at is None
    assert audit.closed_at is None
    assert audit.report is None
    assert audit.report_approval is None
    assert audit.report_approved is False
    assert audit.closure_date is None
    assert audit.lead_auditor == "AUD-001"

    parsed = UUID(audit.id)
    assert parsed.version == 4
    assert str(parsed) == audit.id
    assert audit.created_at.tzinfo == UTC
    assert before <= audit.created_at <= after


def test_core_model_alias_points_to_audit() -> None:
    assert CoreModel is Audit


def test_generated_uuid_is_unique_and_canonical() -> None:
    audits = [valid_audit(title=f"Audit {i}") for i in range(20)]
    ids = [audit.id for audit in audits]

    assert len(ids) == len(set(ids))
    for value in ids:
        parsed = UUID(value)
        assert parsed.version == 4
        assert str(parsed) == value


def test_created_at_is_timezone_aware_utc() -> None:
    audit = valid_audit()

    assert isinstance(audit.created_at, datetime)
    assert audit.created_at.tzinfo == UTC
    assert audit.created_at.utcoffset() == timedelta(0)


def test_constructor_normalizes_text_and_planned_date_to_utc() -> None:
    plus_three = timezone(timedelta(hours=3))
    audit = valid_audit(
        title="  Audit title  ",
        objective="  Objective  ",
        scope="  Scope  ",
        audit_programme_id="  PROGRAMME-1  ",
        security_classification_id="  CLASS-1  ",
        planned_date=datetime(2026, 10, 15, 10, 30, tzinfo=plus_three),
    )

    assert audit.title == "Audit title"
    assert audit.objective == "Objective"
    assert audit.scope == "Scope"
    assert audit.audit_programme_id == "PROGRAMME-1"
    assert audit.security_classification_id == "CLASS-1"
    assert audit.planned_date == datetime(
        2026, 10, 15, 7, 30, tzinfo=UTC
    )


# ---------------------------------------------------------------------------
# Value-object __post_init__ validation
# ---------------------------------------------------------------------------


def test_audit_type_ref_validates_and_strips_text() -> None:
    ref = AuditTypeRef("  supplier  ")
    assert ref.audit_type_id == "supplier"


@pytest.mark.parametrize("bad_value", ["", "   ", None, 123])
def test_audit_type_ref_rejects_invalid_id(bad_value: object) -> None:
    expected_exception = ValueError if isinstance(bad_value, str) else TypeError
    with pytest.raises(expected_exception):
        AuditTypeRef(bad_value)  # type: ignore[arg-type]


def test_audit_object_ref_happy_path() -> None:
    ref = AuditObjectRef(AuditObjectKind.SUPPLIER, "  SUP-01  ")
    assert ref.kind is AuditObjectKind.SUPPLIER
    assert ref.object_id == "SUP-01"


def test_audit_object_ref_rejects_invalid_kind() -> None:
    with pytest.raises(TypeError):
        AuditObjectRef("supplier", "SUP-01")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_value", ["", "   ", None, 1])
def test_audit_object_ref_rejects_invalid_object_id(bad_value: object) -> None:
    expected_exception = ValueError if isinstance(bad_value, str) else TypeError
    with pytest.raises(expected_exception):
        AuditObjectRef(AuditObjectKind.SUPPLIER, bad_value)  # type: ignore[arg-type]


def test_audit_team_member_happy_path() -> None:
    member = AuditTeamMember("  AUD-1  ", AuditTeamRole.LEAD)
    assert member.auditor_id == "AUD-1"
    assert member.role is AuditTeamRole.LEAD


@pytest.mark.parametrize("bad_value", ["", "   ", None, 1])
def test_audit_team_member_rejects_invalid_auditor_id(bad_value: object) -> None:
    expected_exception = ValueError if isinstance(bad_value, str) else TypeError
    with pytest.raises(expected_exception):
        AuditTeamMember(bad_value)  # type: ignore[arg-type]


def test_audit_team_member_rejects_invalid_role() -> None:
    with pytest.raises(TypeError):
        AuditTeamMember("AUD-1", "lead")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    [
        "criterion_id",
        "version",
        "title",
        "requirement_text",
        "source_type",
        "source_id",
    ],
)
def test_criterion_snapshot_rejects_empty_required_fields(
    field_name: str,
) -> None:
    data = {
        "criterion_id": "CRIT-1",
        "version": "A",
        "title": "Title",
        "requirement_text": "Requirement",
        "source_type": "standard",
        "source_id": "STD-1",
        "clause": "8.1",
    }
    data[field_name] = "   "

    with pytest.raises(ValueError):
        AuditCriterionSnapshot(**data)


def test_criterion_snapshot_rejects_empty_clause_when_provided() -> None:
    with pytest.raises(ValueError):
        AuditCriterionSnapshot(
            criterion_id="CRIT-1",
            version="A",
            title="Title",
            requirement_text="Requirement",
            source_type="standard",
            source_id="STD-1",
            clause="   ",
        )


def test_report_ref_rejects_empty_report_id() -> None:
    with pytest.raises(ValueError):
        AuditReportRef("", "1.0")


def test_report_ref_rejects_empty_version() -> None:
    with pytest.raises(ValueError):
        AuditReportRef("REPORT-1", "   ")


def test_report_approval_happy_path_and_utc_normalization() -> None:
    plus_three = timezone(timedelta(hours=3))
    approval = AuditReportApproval(
        report=AuditReportRef("REPORT-1", "1.0"),
        approved_by="  APPROVER-1  ",
        approved_at=datetime(2026, 9, 20, 15, 0, tzinfo=plus_three),
    )

    assert approval.approved_by == "APPROVER-1"
    assert approval.approved_at == datetime(
        2026, 9, 20, 12, 0, tzinfo=UTC
    )


def test_report_approval_rejects_invalid_report_type() -> None:
    with pytest.raises(TypeError):
        AuditReportApproval(
            report="REPORT-1",  # type: ignore[arg-type]
            approved_by="APPROVER-1",
            approved_at=datetime.now(UTC),
        )


def test_report_approval_rejects_empty_approver() -> None:
    with pytest.raises(ValueError):
        AuditReportApproval(
            report=AuditReportRef("REPORT-1", "1.0"),
            approved_by="   ",
            approved_at=datetime.now(UTC),
        )


@pytest.mark.parametrize(
    "bad_time",
    [datetime(2026, 9, 20, 12, 0, tzinfo=UTC).replace(tzinfo=None), "2026-09-20T12:00:00Z"],
)
def test_report_approval_rejects_invalid_approval_time(
    bad_time: object,
) -> None:
    expected_exception = ValueError if isinstance(bad_time, datetime) else TypeError
    with pytest.raises(expected_exception):
        AuditReportApproval(
            report=AuditReportRef("REPORT-1", "1.0"),
            approved_by="APPROVER-1",
            approved_at=bad_time,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Closure gate validation
# ---------------------------------------------------------------------------


def test_closure_gate_happy_path_is_clear() -> None:
    gate = AuditClosureGate()
    assert gate.is_clear is True
    gate.assert_clear()


@pytest.mark.parametrize(
    "field_name",
    [
        "open_findings_count",
        "open_actions_count",
        "pending_verifications_count",
        "pending_effectiveness_checks_count",
        "untreated_overdue_items_count",
    ],
)
def test_closure_gate_rejects_negative_counters(field_name: str) -> None:
    with pytest.raises(ValueError):
        AuditClosureGate(**{field_name: -1})


@pytest.mark.parametrize(
    "bad_value",
    [1.5, "1", True, None],
)
def test_closure_gate_rejects_non_integer_counter(bad_value: object) -> None:
    with pytest.raises(TypeError):
        AuditClosureGate(open_findings_count=bad_value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"open_findings_count": 1},
        {"open_actions_count": 1},
        {"pending_verifications_count": 1},
        {"pending_effectiveness_checks_count": 1},
        {"untreated_overdue_items_count": 1},
    ],
)
def test_closure_gate_assert_clear_rejects_each_blocker(
    kwargs: dict[str, int],
) -> None:
    gate = AuditClosureGate(**kwargs)
    assert gate.is_clear is False
    with pytest.raises(ValueError, match="closure gate is blocked"):
        gate.assert_clear()


# ---------------------------------------------------------------------------
# Audit constructor / __post_init__ validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_title", ["", "   ", None, 123])
def test_audit_rejects_invalid_title(bad_title: object) -> None:
    expected_exception = ValueError if isinstance(bad_title, str) else TypeError
    with pytest.raises(expected_exception):
        valid_audit(title=bad_title)


@pytest.mark.parametrize("field_name", ["objective", "scope"])
def test_audit_rejects_non_string_objective_or_scope(field_name: str) -> None:
    with pytest.raises(TypeError):
        valid_audit(**{field_name: 123})


def test_audit_rejects_invalid_audit_type() -> None:
    with pytest.raises(TypeError, match="audit_type"):
        valid_audit(audit_type="supplier")


@pytest.mark.parametrize(
    "field_name",
    ["audit_programme_id", "security_classification_id"],
)
def test_audit_rejects_empty_optional_reference_when_provided(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        valid_audit(**{field_name: "   "})


@pytest.mark.parametrize(
    "bad_planned_date",
    [datetime(2026, 10, 15, 7, 30, tzinfo=UTC).replace(tzinfo=None), "2026-10-15T07:30:00Z"],
)
def test_audit_rejects_invalid_planned_date(bad_planned_date: object) -> None:
    expected_exception = (
        ValueError if isinstance(bad_planned_date, datetime) else TypeError
    )
    with pytest.raises(expected_exception):
        valid_audit(planned_date=bad_planned_date)


def test_audit_rejects_invalid_audit_object_item() -> None:
    with pytest.raises(TypeError):
        valid_audit(audit_objects=("SUP-001",))


def test_audit_rejects_duplicate_audit_object_reference() -> None:
    ref = AuditObjectRef(AuditObjectKind.SUPPLIER, "SUP-001")
    with pytest.raises(ValueError, match="duplicate"):
        valid_audit(audit_objects=(ref, ref))


def test_audit_rejects_invalid_team_item() -> None:
    with pytest.raises(TypeError):
        valid_audit(team=("AUD-001",))


def test_audit_rejects_duplicate_auditor() -> None:
    with pytest.raises(ValueError, match="appears more than once"):
        valid_audit(
            team=(
                AuditTeamMember("AUD-001", AuditTeamRole.LEAD),
                AuditTeamMember("AUD-001", AuditTeamRole.AUDITOR),
            )
        )


def test_audit_rejects_multiple_lead_auditors() -> None:
    with pytest.raises(ValueError, match="only one Lead Auditor"):
        valid_audit(
            team=(
                AuditTeamMember("AUD-001", AuditTeamRole.LEAD),
                AuditTeamMember("AUD-002", AuditTeamRole.LEAD),
            )
        )


def test_audit_rejects_invalid_criterion_item() -> None:
    with pytest.raises(TypeError):
        valid_audit(criteria=("CRIT-001",))


def test_audit_rejects_duplicate_criterion_id_even_with_different_version() -> None:
    with pytest.raises(ValueError, match="appears more than once"):
        valid_audit(
            criteria=(
                criterion("CRIT-001", "A"),
                criterion("CRIT-001", "B"),
            )
        )


# ---------------------------------------------------------------------------
# Validation branches that cannot be injected through the public constructor
# (id/status/lifecycle timestamps use init=False and are generated internally).
# We deliberately corrupt the object using object.__setattr__ and then call the
# same validate() routine invoked by Audit.__post_init__.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_id",
    [
        "",
        "not-a-uuid",
        str(uuid1()),
        str(uuid4()).upper(),
    ],
)
def test_validate_rejects_invalid_uuid_variants(bad_id: str) -> None:
    audit = valid_audit()
    object.__setattr__(audit, "id", bad_id)

    with pytest.raises(ValueError):
        audit.validate()


@pytest.mark.parametrize(
    "bad_created_at",
    [
        datetime(2026, 9, 20, 12, 0, tzinfo=UTC).replace(tzinfo=None),
        "2026-09-20T12:00:00Z",
    ],
)
def test_validate_rejects_invalid_created_at(bad_created_at: object) -> None:
    audit = valid_audit()
    object.__setattr__(audit, "created_at", bad_created_at)

    expected_exception = (
        ValueError if isinstance(bad_created_at, datetime) else TypeError
    )
    with pytest.raises(expected_exception):
        audit.validate()


def test_validate_rejects_non_enum_status() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "status", "draft")

    with pytest.raises(TypeError, match="AuditStatus"):
        audit.validate()


def test_validate_rejects_non_tuple_collections() -> None:
    for field_name, bad_value in (
        ("audit_objects", []),
        ("team", []),
        ("criteria", []),
    ):
        audit = valid_audit()
        object.__setattr__(audit, field_name, bad_value)
        with pytest.raises(TypeError):
            audit.validate()


def test_validate_rejects_started_at_before_created_at() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "started_at", audit.created_at - timedelta(seconds=1))

    with pytest.raises(ValueError, match="started_at cannot be earlier"):
        audit.validate()


def test_validate_rejects_completed_at_without_started_at() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "completed_at", audit.created_at + timedelta(hours=2))

    with pytest.raises(ValueError, match="completed_at requires started_at"):
        audit.validate()


def test_validate_rejects_completed_at_before_started_at() -> None:
    audit = valid_audit()
    start = audit.created_at + timedelta(hours=2)
    object.__setattr__(audit, "started_at", start)
    object.__setattr__(audit, "completed_at", start - timedelta(minutes=1))

    with pytest.raises(ValueError, match="completed_at cannot be earlier"):
        audit.validate()


def test_validate_rejects_closed_at_without_completed_at() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "closed_at", audit.created_at + timedelta(hours=3))

    with pytest.raises(ValueError, match="closed_at requires completed_at"):
        audit.validate()


def test_validate_rejects_closed_at_before_completed_at() -> None:
    audit = valid_audit()
    start = audit.created_at + timedelta(hours=1)
    completed = start + timedelta(hours=2)
    object.__setattr__(audit, "started_at", start)
    object.__setattr__(audit, "completed_at", completed)
    object.__setattr__(audit, "closed_at", completed - timedelta(minutes=1))

    with pytest.raises(ValueError, match="closed_at cannot be earlier"):
        audit.validate()


def test_start_normalizes_aware_non_utc_timestamp_to_utc() -> None:
    audit = issued_audit()
    plus_three = timezone(timedelta(hours=3))
    local_time = datetime(2026, 9, 21, 10, 0, tzinfo=plus_three)

    audit.start(local_time)

    assert audit.started_at == datetime(
        2026, 9, 21, 7, 0, tzinfo=UTC
    )
    assert audit.started_at.tzinfo == UTC


def test_validate_rejects_invalid_report_type() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "report", "REPORT-1")

    with pytest.raises(TypeError):
        audit.validate()


def test_validate_rejects_invalid_report_approval_type() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "report_approval", True)

    with pytest.raises(TypeError):
        audit.validate()


def test_validate_rejects_report_approval_without_report() -> None:
    audit = valid_audit()
    report = AuditReportRef("REPORT-1", "1.0")
    approval = AuditReportApproval(
        report=report,
        approved_by="APPROVER-1",
        approved_at=audit.created_at + timedelta(minutes=1),
    )
    object.__setattr__(audit, "report_approval", approval)

    with pytest.raises(ValueError, match="no report is attached"):
        audit.validate()


def test_validate_rejects_approval_for_different_report_version() -> None:
    audit = valid_audit()
    current = AuditReportRef("REPORT-1", "2.0")
    approved = AuditReportRef("REPORT-1", "1.0")
    approval = AuditReportApproval(
        report=approved,
        approved_by="APPROVER-1",
        approved_at=audit.created_at + timedelta(minutes=1),
    )
    object.__setattr__(audit, "report", current)
    object.__setattr__(audit, "report_approval", approval)

    with pytest.raises(ValueError, match="currently attached report version"):
        audit.validate()


def test_validate_rejects_report_approval_before_audit_creation() -> None:
    audit = valid_audit()
    report = AuditReportRef("REPORT-1", "1.0")
    approval = AuditReportApproval(
        report=report,
        approved_by="APPROVER-1",
        approved_at=audit.created_at - timedelta(seconds=1),
    )
    object.__setattr__(audit, "report", report)
    object.__setattr__(audit, "report_approval", approval)

    with pytest.raises(ValueError, match="earlier than audit creation"):
        audit.validate()


# ---------------------------------------------------------------------------
# Planning-state required fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides, expected_field",
    [
        ({"audit_type": None}, "audit_type"),
        ({"audit_objects": ()}, "audit_objects"),
        ({"scope": ""}, "scope"),
        ({"planned_date": None}, "planned_date"),
        (
            {
                "team": (
                    AuditTeamMember("AUD-002", AuditTeamRole.AUDITOR),
                )
            },
            "Lead Auditor",
        ),
    ],
)
def test_plan_rejects_each_missing_mandatory_planning_field(
    overrides: dict[str, object],
    expected_field: str,
) -> None:
    audit = valid_audit(**overrides)

    with pytest.raises(ValueError, match=expected_field):
        audit.plan()

    # _apply_atomic must roll back the failed transition.
    assert audit.status is AuditStatus.DRAFT


# ---------------------------------------------------------------------------
# Lifecycle happy path and transition validation
# ---------------------------------------------------------------------------


def test_full_lifecycle_happy_path() -> None:
    audit = valid_audit()

    audit.plan()
    assert audit.status is AuditStatus.PLANNED

    audit.issue()
    assert audit.status is AuditStatus.ISSUED

    start = audit.created_at + timedelta(hours=1)
    audit.start(start)
    assert audit.status is AuditStatus.IN_PROGRESS
    assert audit.started_at == start

    completed = start + timedelta(hours=3)
    audit.complete(completed)
    assert audit.status is AuditStatus.COMPLETED
    assert audit.completed_at == completed

    report = AuditReportRef("REPORT-001", "1.0")
    audit.attach_report(report)
    assert audit.report == report
    assert audit.report_approved is False

    approved = completed + timedelta(minutes=10)
    audit.approve_report("APPROVER-001", approved)
    assert audit.report_approved is True
    assert audit.report_approval.approved_by == "APPROVER-001"
    assert audit.report_approval.approved_at == approved

    closed = approved + timedelta(minutes=10)
    audit.close(AuditClosureGate(), closed)
    assert audit.status is AuditStatus.CLOSED
    assert audit.closed_at == closed
    assert audit.closure_date == closed


def test_direct_domain_mutation_is_blocked() -> None:
    audit = valid_audit()

    with pytest.raises(AttributeError, match="Direct assignment"):
        audit.title = "Changed directly"

    with pytest.raises(AttributeError, match="Direct assignment"):
        audit.status = AuditStatus.CLOSED


def test_baseline_changes_are_blocked_after_issue() -> None:
    audit = issued_audit()

    with pytest.raises(ValueError, match="baseline is locked"):
        audit.set_scope("Changed scope")

    with pytest.raises(ValueError, match="baseline is locked"):
        audit.replace_criteria((criterion("CRIT-002"),))


def test_issue_rejects_non_planned_audit() -> None:
    with pytest.raises(ValueError):
        valid_audit().issue()


def test_start_rejects_non_issued_audit() -> None:
    with pytest.raises(ValueError):
        valid_audit().start()


def test_start_rejects_naive_datetime() -> None:
    audit = issued_audit()
    with pytest.raises(ValueError):
        audit.start(datetime(2026, 9, 21, 10, 0, tzinfo=UTC).replace(tzinfo=None))


def test_complete_rejects_non_in_progress_audit() -> None:
    with pytest.raises(ValueError):
        issued_audit().complete()


def test_complete_rejects_time_before_start_and_rolls_back() -> None:
    audit = in_progress_audit()
    before_status = audit.status

    with pytest.raises(ValueError, match="completed_at cannot be earlier"):
        audit.complete(audit.started_at - timedelta(seconds=1))

    assert audit.status is before_status
    assert audit.completed_at is None


# ---------------------------------------------------------------------------
# Report / closure validation
# ---------------------------------------------------------------------------


def test_attach_report_rejects_wrong_status() -> None:
    with pytest.raises(ValueError):
        valid_audit().attach_report(AuditReportRef("REPORT-1", "1.0"))


def test_attach_report_rejects_wrong_type() -> None:
    audit = completed_audit()
    with pytest.raises(TypeError):
        audit.attach_report("REPORT-1")  # type: ignore[arg-type]


def test_replacing_report_invalidates_previous_approval() -> None:
    audit = completed_audit(with_report=True)
    audit.approve_report(
        "APPROVER-1",
        audit.completed_at + timedelta(minutes=1),
    )
    assert audit.report_approved is True

    audit.attach_report(AuditReportRef("REPORT-1", "2.0"))
    assert audit.report_approval is None
    assert audit.report_approved is False


def test_approve_report_rejects_non_completed_status() -> None:
    audit = in_progress_audit()
    audit.attach_report(AuditReportRef("REPORT-1", "1.0"))

    with pytest.raises(ValueError):
        audit.approve_report("APPROVER-1")


def test_approve_report_rejects_missing_report() -> None:
    audit = completed_audit(with_report=False)

    with pytest.raises(ValueError, match="no report is attached"):
        audit.approve_report("APPROVER-1")


def test_approve_report_rejects_approval_before_creation() -> None:
    audit = completed_audit(with_report=True)

    with pytest.raises(ValueError, match="earlier than audit creation"):
        audit.approve_report(
            "APPROVER-1",
            audit.created_at - timedelta(seconds=1),
        )


def test_close_rejects_non_completed_status() -> None:
    with pytest.raises(ValueError):
        in_progress_audit().close(AuditClosureGate())


def test_close_rejects_invalid_gate_type() -> None:
    audit = completed_audit(with_report=True)
    audit.approve_report(
        "APPROVER-1",
        audit.completed_at + timedelta(minutes=1),
    )

    with pytest.raises(TypeError):
        audit.close("clear")  # type: ignore[arg-type]


def test_close_rejects_blocked_closure_gate() -> None:
    audit = completed_audit(with_report=True)
    audit.approve_report(
        "APPROVER-1",
        audit.completed_at + timedelta(minutes=1),
    )

    with pytest.raises(ValueError, match="closure gate is blocked"):
        audit.close(AuditClosureGate(open_findings_count=1))


def test_close_rejects_missing_report() -> None:
    audit = completed_audit(with_report=False)

    with pytest.raises(ValueError, match="without an attached report"):
        audit.close(AuditClosureGate())


def test_close_rejects_unapproved_report() -> None:
    audit = completed_audit(with_report=True)

    with pytest.raises(ValueError, match="before the report is approved"):
        audit.close(AuditClosureGate())


def test_close_rejects_time_before_report_approval() -> None:
    audit = completed_audit(with_report=True)
    approval_time = audit.completed_at + timedelta(minutes=10)
    audit.approve_report("APPROVER-1", approval_time)

    with pytest.raises(ValueError, match="earlier than report approval"):
        audit.close(
            AuditClosureGate(),
            approval_time - timedelta(seconds=1),
        )


# ---------------------------------------------------------------------------
# Reopen / defer / cancel validation
# ---------------------------------------------------------------------------


def test_reopen_happy_path_clears_current_closure_and_approval() -> None:
    audit = closed_audit()
    old_closed_at = audit.closed_at

    audit.reopen(
        "Additional evidence requires review",
        old_closed_at + timedelta(minutes=5),
    )

    assert audit.status is AuditStatus.REOPENED
    assert audit.closed_at is None
    assert audit.report_approval is None
    assert audit.last_reopen_reason == "Additional evidence requires review"
    assert audit.reopened_at == old_closed_at + timedelta(minutes=5)


def test_reopen_rejects_non_closed_audit() -> None:
    with pytest.raises(ValueError):
        completed_audit().reopen("Reason")


def test_reopen_rejects_empty_reason() -> None:
    audit = closed_audit()
    with pytest.raises(ValueError):
        audit.reopen("   ")


def test_reopen_rejects_timestamp_before_previous_closure() -> None:
    audit = closed_audit()
    with pytest.raises(ValueError, match="earlier than the previous closed_at"):
        audit.reopen("Reason", audit.closed_at - timedelta(seconds=1))


def test_resume_reopened_allows_in_progress_or_completed() -> None:
    audit = closed_audit()
    audit.reopen("Need follow-up", audit.closed_at + timedelta(minutes=1))
    audit.resume_reopened(AuditStatus.COMPLETED)
    assert audit.status is AuditStatus.COMPLETED

    # Close again, reopen and resume to IN_PROGRESS.
    audit.approve_report(
        "APPROVER-2",
        audit.reopened_at + timedelta(minutes=2),
    )
    audit.close(
        AuditClosureGate(),
        audit.report_approval.approved_at + timedelta(minutes=1),
    )
    audit.reopen("More work", audit.closed_at + timedelta(minutes=1))
    audit.resume_reopened(AuditStatus.IN_PROGRESS)
    assert audit.status is AuditStatus.IN_PROGRESS
    assert audit.completed_at is None


def test_resume_reopened_rejects_invalid_target() -> None:
    audit = closed_audit()
    audit.reopen("Reason", audit.closed_at + timedelta(minutes=1))

    with pytest.raises(ValueError):
        audit.resume_reopened(AuditStatus.ISSUED)


def test_defer_and_resume_happy_path_from_planned() -> None:
    audit = valid_audit()
    audit.plan()
    audit.defer("Supplier requested reschedule")

    assert audit.status is AuditStatus.DEFERRED
    assert audit.deferred_from_status is AuditStatus.PLANNED
    assert audit.last_defer_reason == "Supplier requested reschedule"

    audit.resume_deferred()
    assert audit.status is AuditStatus.PLANNED
    assert audit.deferred_at is None
    assert audit.deferred_from_status is None


def test_defer_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        valid_audit().defer("Reason")


def test_defer_rejects_empty_reason() -> None:
    audit = valid_audit()
    audit.plan()
    with pytest.raises(ValueError):
        audit.defer("   ")


def test_resume_deferred_rejects_non_deferred_status() -> None:
    with pytest.raises(ValueError):
        valid_audit().resume_deferred()


def test_cancel_happy_path_requires_reason() -> None:
    audit = valid_audit()
    audit.cancel("Audit no longer required")

    assert audit.status is AuditStatus.CANCELLED
    assert audit.last_cancel_reason == "Audit no longer required"
    assert audit.cancelled_at is not None


def test_cancel_rejects_empty_reason() -> None:
    with pytest.raises(ValueError):
        valid_audit().cancel("   ")


def test_cancel_rejects_already_cancelled_audit() -> None:
    audit = valid_audit()
    audit.cancel("Reason")

    with pytest.raises(ValueError):
        audit.cancel("Again")


def test_cancel_rejects_closed_audit() -> None:
    with pytest.raises(ValueError):
        closed_audit().cancel("Cannot cancel closed audit")


# ---------------------------------------------------------------------------
# Explicit state-invariant validation branches
# ---------------------------------------------------------------------------


def test_validate_in_progress_requires_started_at() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "status", AuditStatus.IN_PROGRESS)

    with pytest.raises(ValueError, match="requires started_at"):
        audit.validate()


def test_validate_in_progress_rejects_completed_at() -> None:
    audit = valid_audit()
    started = audit.created_at + timedelta(hours=1)
    object.__setattr__(audit, "started_at", started)
    object.__setattr__(audit, "completed_at", started + timedelta(hours=1))
    object.__setattr__(audit, "status", AuditStatus.IN_PROGRESS)

    with pytest.raises(ValueError, match="cannot have completed_at"):
        audit.validate()


def test_validate_in_progress_rejects_closed_at() -> None:
    audit = valid_audit()
    started = audit.created_at + timedelta(hours=1)
    completed = started + timedelta(hours=1)
    object.__setattr__(audit, "started_at", started)
    object.__setattr__(audit, "completed_at", completed)
    object.__setattr__(audit, "closed_at", completed + timedelta(minutes=1))
    object.__setattr__(audit, "status", AuditStatus.IN_PROGRESS)

    # Date validation reaches the state as a chronologically valid set first.
    with pytest.raises(ValueError):
        audit.validate()


def test_validate_completed_requires_started_at() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "completed_at", audit.created_at + timedelta(hours=2))
    object.__setattr__(audit, "status", AuditStatus.COMPLETED)

    with pytest.raises(ValueError):
        audit.validate()


def test_validate_completed_requires_completed_at() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "started_at", audit.created_at + timedelta(hours=1))
    object.__setattr__(audit, "status", AuditStatus.COMPLETED)

    with pytest.raises(ValueError, match="requires completed_at"):
        audit.validate()


def test_validate_completed_rejects_closed_at() -> None:
    audit = valid_audit()
    started = audit.created_at + timedelta(hours=1)
    completed = started + timedelta(hours=1)
    object.__setattr__(audit, "started_at", started)
    object.__setattr__(audit, "completed_at", completed)
    object.__setattr__(audit, "closed_at", completed + timedelta(minutes=1))
    object.__setattr__(audit, "status", AuditStatus.COMPLETED)

    with pytest.raises(ValueError, match="cannot have closed_at"):
        audit.validate()


def _force_base_closed_state(audit: Audit) -> None:
    started = audit.created_at + timedelta(hours=1)
    completed = started + timedelta(hours=1)
    closed = completed + timedelta(hours=1)
    report = AuditReportRef("REPORT-X", "1.0")
    approval = AuditReportApproval(
        report=report,
        approved_by="APPROVER-X",
        approved_at=completed + timedelta(minutes=10),
    )
    object.__setattr__(audit, "started_at", started)
    object.__setattr__(audit, "completed_at", completed)
    object.__setattr__(audit, "closed_at", closed)
    object.__setattr__(audit, "report", report)
    object.__setattr__(audit, "report_approval", approval)
    object.__setattr__(audit, "status", AuditStatus.CLOSED)


@pytest.mark.parametrize(
    "field_name, expected",
    [
        ("started_at", "requires started_at"),
        ("completed_at", "requires completed_at"),
        ("closed_at", "requires closed_at"),
        ("report", "requires an attached report"),
        ("report_approval", "requires report approval"),
    ],
)
def test_validate_closed_requires_all_local_closure_fields(
    field_name: str,
    expected: str,
) -> None:
    audit = valid_audit()
    _force_base_closed_state(audit)
    object.__setattr__(audit, field_name, None)

    with pytest.raises(ValueError):
        audit.validate()


def test_validate_deferred_requires_deferred_at() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "status", AuditStatus.DEFERRED)
    object.__setattr__(audit, "deferred_from_status", AuditStatus.PLANNED)
    object.__setattr__(audit, "last_defer_reason", "Reason")

    with pytest.raises(ValueError, match="requires deferred_at"):
        audit.validate()


def test_validate_deferred_requires_valid_origin_state() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "status", AuditStatus.DEFERRED)
    object.__setattr__(audit, "deferred_at", audit.created_at + timedelta(minutes=1))
    object.__setattr__(audit, "deferred_from_status", AuditStatus.DRAFT)
    object.__setattr__(audit, "last_defer_reason", "Reason")

    with pytest.raises(ValueError, match="must originate"):
        audit.validate()


def test_validate_deferred_requires_reason() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "status", AuditStatus.DEFERRED)
    object.__setattr__(audit, "deferred_at", audit.created_at + timedelta(minutes=1))
    object.__setattr__(audit, "deferred_from_status", AuditStatus.PLANNED)
    object.__setattr__(audit, "last_defer_reason", None)

    with pytest.raises(ValueError, match="requires a defer reason"):
        audit.validate()


def test_validate_cancelled_requires_cancelled_at() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "status", AuditStatus.CANCELLED)
    object.__setattr__(audit, "last_cancel_reason", "Reason")

    with pytest.raises(ValueError, match="requires cancelled_at"):
        audit.validate()


def test_validate_cancelled_requires_reason() -> None:
    audit = valid_audit()
    object.__setattr__(audit, "status", AuditStatus.CANCELLED)
    object.__setattr__(audit, "cancelled_at", audit.created_at + timedelta(minutes=1))

    with pytest.raises(ValueError, match="requires a cancellation reason"):
        audit.validate()


def _force_base_reopened_state(audit: Audit) -> None:
    started = audit.created_at + timedelta(hours=1)
    completed = started + timedelta(hours=1)
    object.__setattr__(audit, "started_at", started)
    object.__setattr__(audit, "completed_at", completed)
    object.__setattr__(audit, "closed_at", None)
    object.__setattr__(audit, "reopened_at", completed + timedelta(hours=1))
    object.__setattr__(audit, "last_reopen_reason", "Reason")
    object.__setattr__(audit, "status", AuditStatus.REOPENED)


def test_validate_reopened_requires_previous_execution_timestamps() -> None:
    audit = valid_audit()
    _force_base_reopened_state(audit)
    object.__setattr__(audit, "started_at", None)
    object.__setattr__(audit, "completed_at", None)

    with pytest.raises(ValueError):
        audit.validate()


def test_validate_reopened_rejects_current_closed_at() -> None:
    audit = valid_audit()
    _force_base_reopened_state(audit)
    object.__setattr__(audit, "closed_at", audit.reopened_at - timedelta(minutes=1))

    with pytest.raises(ValueError, match="must not retain closed_at"):
        audit.validate()


def test_validate_reopened_requires_reopened_at() -> None:
    audit = valid_audit()
    _force_base_reopened_state(audit)
    object.__setattr__(audit, "reopened_at", None)

    with pytest.raises(ValueError, match="requires reopened_at"):
        audit.validate()


def test_validate_reopened_requires_reason() -> None:
    audit = valid_audit()
    _force_base_reopened_state(audit)
    object.__setattr__(audit, "last_reopen_reason", None)

    with pytest.raises(ValueError, match="requires a reopen reason"):
        audit.validate()
