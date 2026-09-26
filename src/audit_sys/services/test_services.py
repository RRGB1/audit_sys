"""Unit and integration tests for ``AuditService``.

Integration tests inject a real ``JsonAuditRepository`` located in an isolated
``tmp_path`` directory. Unit tests inject an in-memory spy repository to check
the service's orchestration and error propagation independently of JSON.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from audit_sys.models.core import (
    Audit,
    AuditObjectKind,
    AuditObjectRef,
    AuditStatus,
    AuditTeamMember,
    AuditTeamRole,
    AuditTypeRef,
)
from audit_sys.services.audit_service import (
    AuditService,
    AuditServiceError,
    DomainValidationError,
)
from audit_sys.storage.base import AuditRepository, NotFoundError, StorageError
from audit_sys.storage.json_storage import JsonAuditRepository

UTC_PLUS_THREE = timezone(timedelta(hours=3))

# ---------------------------------------------------------------------------
# Test doubles, helpers and fixtures
# ---------------------------------------------------------------------------


class SpyAuditRepository(AuditRepository):
    """In-memory repository that records calls and can simulate failures."""

    def __init__(self, failure: StorageError | None = None) -> None:
        self.items: dict[str, Audit] = {}
        self.calls: list[str] = []
        self.failure = failure

    def _record(self, operation: str) -> None:
        self.calls.append(operation)
        if self.failure is not None:
            raise self.failure

    def save(self, item: Audit) -> None:
        self._record("save")
        self.items[item.id] = item

    def get_by_id(self, item_id: UUID) -> Audit | None:
        self._record("get_by_id")
        return self.items.get(str(item_id))

    def list_all(self) -> list[Audit]:
        self._record("list_all")
        # Reverse insertion order to prove the service sorts the result.
        return list(reversed(self.items.values()))

    def delete(self, item_id: UUID) -> None:
        self._record("delete")
        if self.items.pop(str(item_id), None) is None:
            raise NotFoundError("Audit", item_id)


def _planning_data() -> dict[str, Any]:
    """Return complete planning input accepted by ``create_audit``."""
    return {
        "objective": "Verify supplier control",
        "scope": "Production line A",
        "audit_type": AuditTypeRef("internal"),
        "audit_programme_id": "PRG-2026",
        "audit_objects": [AuditObjectRef(AuditObjectKind.SUPPLIER, "SUP-1")],
        "team": [AuditTeamMember("auditor-1", AuditTeamRole.LEAD)],
        "planned_date": datetime(2026, 11, 1, 9, 0, tzinfo=UTC_PLUS_THREE),
        "security_classification_id": "internal",
    }


def _create_with_status(
    service: AuditService,
    storage: AuditRepository,
    title: str,
    status: AuditStatus,
) -> Audit:
    """Create an audit through the service and move it to ``status``."""
    audit = service.create_audit(title, **_planning_data())
    if status is AuditStatus.DRAFT:
        return audit

    audit.plan()
    if status is AuditStatus.ISSUED:
        audit.issue()
    elif status is AuditStatus.CANCELLED:
        audit.cancel("No longer required")
    elif status is not AuditStatus.PLANNED:
        raise AssertionError(f"Unsupported status in test helper: {status}")

    storage.save(audit)
    return audit


@pytest.fixture
def storage(tmp_path: Path) -> JsonAuditRepository:
    """Return a JSON repository in an isolated temporary directory."""
    return JsonAuditRepository(tmp_path / "data")


@pytest.fixture
def service(storage: JsonAuditRepository) -> AuditService:
    """Return an ``AuditService`` wired to the temporary JSON repository."""
    return AuditService(storage)


@pytest.fixture
def mixed_audits(
    service: AuditService,
    storage: JsonAuditRepository,
) -> dict[AuditStatus, list[Audit]]:
    """Store audits in several statuses and return them grouped by status."""
    return {
        AuditStatus.DRAFT: [
            _create_with_status(service, storage, "Draft 1", AuditStatus.DRAFT),
            _create_with_status(service, storage, "Draft 2", AuditStatus.DRAFT),
        ],
        AuditStatus.PLANNED: [
            _create_with_status(service, storage, "Planned 1", AuditStatus.PLANNED),
        ],
        AuditStatus.ISSUED: [
            _create_with_status(service, storage, "Issued 1", AuditStatus.ISSUED),
        ],
        AuditStatus.CANCELLED: [
            _create_with_status(service, storage, "Cancelled 1", AuditStatus.CANCELLED),
        ],
    }


def _by_creation(audits: list[Audit]) -> list[Audit]:
    """Sort audits the same way the service orders its results."""
    return sorted(audits, key=lambda audit: (audit.created_at, audit.id))


# ---------------------------------------------------------------------------
# Construction and dependency injection
# ---------------------------------------------------------------------------


def test_service_accepts_any_audit_repository_implementation() -> None:
    spy = SpyAuditRepository()
    service = AuditService(spy)

    audit = service.create_audit("Audit with spy storage")

    assert spy.calls == ["save"]
    assert spy.items == {audit.id: audit}


# ---------------------------------------------------------------------------
# create_audit & get_audit
# ---------------------------------------------------------------------------


def test_create_audit_returns_new_draft_with_uuid4_and_utc_timestamp(
    service: AuditService,
) -> None:
    before = datetime.now(UTC)

    audit = service.create_audit("  ISO 9001 internal audit  ")

    assert audit.title == "ISO 9001 internal audit"
    assert audit.status is AuditStatus.DRAFT
    assert UUID(audit.id).version == 4
    assert audit.created_at.utcoffset() == timedelta(0)
    assert before <= audit.created_at <= datetime.now(UTC)


def test_create_audit_persists_the_audit(
    service: AuditService,
    storage: JsonAuditRepository,
) -> None:
    audit = service.create_audit("Persisted audit", **_planning_data())

    assert storage.get_by_id(UUID(audit.id)) == audit


def test_create_audit_with_full_planning_data(service: AuditService) -> None:
    audit = service.create_audit("מבדק ספקים", **_planning_data())

    assert audit.title == "מבדק ספקים"
    assert audit.audit_type == AuditTypeRef("internal")
    assert audit.lead_auditor == "auditor-1"
    assert audit.audit_objects == (AuditObjectRef(AuditObjectKind.SUPPLIER, "SUP-1"),)
    assert audit.planned_date == datetime(2026, 11, 1, 6, 0, tzinfo=UTC)


def test_create_then_get_audit_returns_equal_stored_copy(
    service: AuditService,
) -> None:
    created = service.create_audit("Round trip", **_planning_data())

    loaded = service.get_audit(UUID(created.id))

    assert loaded == created
    assert loaded is not created


def test_created_audits_have_unique_ids(service: AuditService) -> None:
    ids = {service.create_audit(f"Audit {index}").id for index in range(10)}

    assert len(ids) == 10


def test_data_is_shared_between_service_instances(tmp_path: Path) -> None:
    created = AuditService(JsonAuditRepository(tmp_path)).create_audit("Shared")

    other_service = AuditService(JsonAuditRepository(tmp_path))

    assert other_service.get_audit(UUID(created.id)) == created


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": ""},
        {"title": "   "},
        {"title": 123},
        {"objective": None},
        {"planned_date": datetime(2026, 11, 1, 9, 0)},  # noqa: DTZ001
        {"planned_date": "2026-11-01"},
        {"audit_type": "internal"},
        {"audit_programme_id": "   "},
        {
            "team": [
                AuditTeamMember("auditor-1", AuditTeamRole.LEAD),
                AuditTeamMember("auditor-2", AuditTeamRole.LEAD),
            ]
        },
        {"team": [AuditTeamMember("auditor-1"), AuditTeamMember("auditor-1")]},
        {
            "audit_objects": [
                AuditObjectRef(AuditObjectKind.SITE, "SITE-1"),
                AuditObjectRef(AuditObjectKind.SITE, "SITE-1"),
            ]
        },
        {"audit_objects": ["not-an-object-ref"]},
        {"criteria": 42},
    ],
    ids=[
        "empty-title",
        "blank-title",
        "non-string-title",
        "none-objective",
        "naive-planned-date",
        "string-planned-date",
        "string-audit-type",
        "blank-programme-id",
        "two-lead-auditors",
        "duplicate-auditor",
        "duplicate-audit-object",
        "invalid-audit-object",
        "non-iterable-criteria",
    ],
)
def test_create_audit_rejects_invalid_input_and_persists_nothing(
    service: AuditService,
    storage: JsonAuditRepository,
    overrides: dict[str, Any],
) -> None:
    arguments: dict[str, Any] = {"title": "Valid title", **overrides}

    with pytest.raises(DomainValidationError, match="Cannot create audit"):
        service.create_audit(**arguments)

    assert storage.list_all() == []


def test_domain_validation_error_is_value_error_and_keeps_cause(
    service: AuditService,
) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        service.create_audit("")

    assert isinstance(exc_info.value, ValueError)
    assert isinstance(exc_info.value, AuditServiceError)
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert "title cannot be empty" in str(exc_info.value)


def test_create_audit_does_not_call_storage_when_input_is_invalid() -> None:
    spy = SpyAuditRepository()

    with pytest.raises(DomainValidationError):
        AuditService(spy).create_audit("")

    assert spy.calls == []


# ---------------------------------------------------------------------------
# list_audits
# ---------------------------------------------------------------------------


def test_list_audits_returns_empty_list_when_no_audits(service: AuditService) -> None:
    assert service.list_audits() == []


def test_list_audits_without_filter_returns_all_ordered_by_creation(
    service: AuditService,
    mixed_audits: dict[AuditStatus, list[Audit]],
) -> None:
    every_audit = [audit for group in mixed_audits.values() for audit in group]

    assert service.list_audits() == _by_creation(every_audit)


@pytest.mark.parametrize(
    "status",
    [AuditStatus.DRAFT, AuditStatus.PLANNED, AuditStatus.ISSUED, AuditStatus.CANCELLED],
)
def test_list_audits_filters_by_status(
    service: AuditService,
    mixed_audits: dict[AuditStatus, list[Audit]],
    status: AuditStatus,
) -> None:
    result = service.list_audits(status=status.value)

    assert result == _by_creation(mixed_audits[status])
    assert all(audit.status is status for audit in result)


@pytest.mark.parametrize(
    "status_filter",
    ["planned", "PLANNED", "  Planned  ", AuditStatus.PLANNED],
)
def test_list_audits_status_filter_is_case_and_whitespace_insensitive(
    service: AuditService,
    mixed_audits: dict[AuditStatus, list[Audit]],
    status_filter: str | AuditStatus,
) -> None:
    assert (
        service.list_audits(status=status_filter) == mixed_audits[AuditStatus.PLANNED]
    )


def test_list_audits_returns_empty_list_when_no_audit_matches(
    service: AuditService,
    mixed_audits: dict[AuditStatus, list[Audit]],
) -> None:
    assert AuditStatus.CLOSED not in mixed_audits
    assert service.list_audits(status="closed") == []


@pytest.mark.parametrize("status_filter", ["", "   ", "archived", "in progress"])
def test_list_audits_rejects_unknown_status(
    service: AuditService,
    status_filter: str,
) -> None:
    with pytest.raises(DomainValidationError, match="Allowed values") as exc_info:
        service.list_audits(status=status_filter)

    assert "in_progress" in str(exc_info.value)


def test_list_audits_rejects_non_string_status(service: AuditService) -> None:
    with pytest.raises(DomainValidationError, match="status must be"):
        service.list_audits(status=1)  # type: ignore[arg-type]


def test_list_audits_validates_status_before_reading_storage() -> None:
    spy = SpyAuditRepository()

    with pytest.raises(DomainValidationError):
        AuditService(spy).list_audits(status="unknown")

    assert spy.calls == []


def test_list_audits_orders_results_independently_of_storage_order() -> None:
    service = AuditService(SpyAuditRepository())
    created = [service.create_audit(f"Audit {index}") for index in range(5)]

    assert service.list_audits() == _by_creation(created)


# ---------------------------------------------------------------------------
# delete_audit
# ---------------------------------------------------------------------------


def test_delete_audit_removes_only_the_requested_audit(
    service: AuditService,
) -> None:
    kept = service.create_audit("Kept audit")
    removed = service.create_audit("Removed audit")

    service.delete_audit(UUID(removed.id))

    assert service.list_audits() == [kept]
    with pytest.raises(NotFoundError):
        service.get_audit(UUID(removed.id))


def test_delete_audit_is_persisted(
    service: AuditService,
    storage: JsonAuditRepository,
) -> None:
    audit = service.create_audit("Audit to delete")

    service.delete_audit(UUID(audit.id))

    assert storage.get_by_id(UUID(audit.id)) is None


# ---------------------------------------------------------------------------
# Error scenarios: unknown identifiers and invalid identifiers
# ---------------------------------------------------------------------------


def test_get_audit_with_unknown_id_raises_not_found_error(
    service: AuditService,
) -> None:
    service.create_audit("Existing audit")
    missing_id = uuid4()

    with pytest.raises(NotFoundError) as exc_info:
        service.get_audit(missing_id)

    assert exc_info.value.entity_name == "Audit"
    assert exc_info.value.item_id == missing_id
    assert str(missing_id) in str(exc_info.value)


def test_delete_audit_with_unknown_id_raises_not_found_error(
    service: AuditService,
) -> None:
    missing_id = uuid4()

    with pytest.raises(NotFoundError) as exc_info:
        service.delete_audit(missing_id)

    assert exc_info.value.item_id == missing_id


def test_deleting_the_same_audit_twice_raises_not_found_error(
    service: AuditService,
) -> None:
    audit = service.create_audit("Audit")
    service.delete_audit(UUID(audit.id))

    with pytest.raises(NotFoundError):
        service.delete_audit(UUID(audit.id))


def test_not_found_error_can_be_handled_as_storage_error(
    service: AuditService,
) -> None:
    with pytest.raises(StorageError):
        service.get_audit(uuid4())


@pytest.mark.parametrize("bad_id", ["not-a-uuid", None, 42])
def test_get_audit_rejects_non_uuid_identifier(
    service: AuditService,
    bad_id: object,
) -> None:
    with pytest.raises(DomainValidationError, match=r"audit_id must be a uuid\.UUID"):
        service.get_audit(bad_id)  # type: ignore[arg-type]


def test_get_audit_rejects_uuid_string_identifier(service: AuditService) -> None:
    audit = service.create_audit("Audit")

    with pytest.raises(DomainValidationError):
        service.get_audit(audit.id)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_id", ["not-a-uuid", None, 42])
def test_delete_audit_rejects_non_uuid_identifier(
    service: AuditService,
    bad_id: object,
) -> None:
    with pytest.raises(DomainValidationError, match=r"audit_id must be a uuid\.UUID"):
        service.delete_audit(bad_id)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Error scenarios: storage failures propagate unchanged
# ---------------------------------------------------------------------------


STORAGE_OPERATIONS: dict[str, Callable[[AuditService], object]] = {
    "create_audit": lambda service: service.create_audit("Audit"),
    "get_audit": lambda service: service.get_audit(uuid4()),
    "list_audits": lambda service: service.list_audits(),
    "delete_audit": lambda service: service.delete_audit(uuid4()),
}


@pytest.mark.parametrize("operation", list(STORAGE_OPERATIONS))
def test_storage_errors_propagate_from_every_use_case(operation: str) -> None:
    failure = StorageError("simulated storage outage")
    service = AuditService(SpyAuditRepository(failure=failure))
    run_operation = STORAGE_OPERATIONS[operation]

    with pytest.raises(StorageError) as exc_info:
        run_operation(service)

    assert exc_info.value is failure


def test_corrupted_json_storage_surfaces_storage_error(
    service: AuditService,
    storage: JsonAuditRepository,
) -> None:
    storage.file_path.write_text("{corrupted", encoding="utf-8")

    with pytest.raises(StorageError, match="valid JSON"):
        service.list_audits()
