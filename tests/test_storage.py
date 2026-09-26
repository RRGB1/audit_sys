"""Unit tests for the JSON storage adapter (``JsonAuditRepository``).

Every test runs against an isolated temporary directory provided by the
``tmp_path`` fixture, so the project's real ``data/`` directory is never
touched.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from filelock import FileLock

from audit_sys.models.core import (
    Audit,
    AuditClosureGate,
    AuditCriterionSnapshot,
    AuditObjectKind,
    AuditObjectRef,
    AuditReportRef,
    AuditStatus,
    AuditTeamMember,
    AuditTeamRole,
    AuditTypeRef,
)
from audit_sys.storage.base import AuditRepository, NotFoundError, StorageError
from audit_sys.storage.json_storage import (
    DEFAULT_FILE_NAME,
    SCHEMA_VERSION,
    JsonAuditRepository,
)

UTC_PLUS_THREE = timezone(timedelta(hours=3))

# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------


def _uuid(audit: Audit) -> UUID:
    """Return the audit identifier as a ``uuid.UUID``."""
    return UUID(audit.id)


def _read_document(repository: JsonAuditRepository) -> dict[str, Any]:
    """Load the raw JSON document written by the repository."""
    document: dict[str, Any] = json.loads(
        repository.file_path.read_text(encoding="utf-8")
    )
    return document


def _write_document(repository: JsonAuditRepository, document: object) -> None:
    """Overwrite the data file with an arbitrary JSON document."""
    repository.file_path.write_text(json.dumps(document), encoding="utf-8")


def _make_draft_audit() -> Audit:
    """Create a minimal DRAFT audit."""
    return Audit(title="Draft audit")


def _make_planned_audit() -> Audit:
    """Create a PLANNED audit with every planning field populated."""
    audit = Audit(
        title="מבדק פנימי ISO 9001",
        objective="Verify supplier control",
        scope="Production line A",
        audit_type=AuditTypeRef("internal"),
        audit_programme_id="PRG-2026",
        audit_objects=(
            AuditObjectRef(AuditObjectKind.PROCESS, "PROC-7"),
            AuditObjectRef(AuditObjectKind.SUPPLIER, "SUP-1"),
        ),
        team=(
            AuditTeamMember("auditor-1", AuditTeamRole.LEAD),
            AuditTeamMember("auditor-2"),
        ),
        criteria=(
            AuditCriterionSnapshot(
                criterion_id="ISO9001-8.4",
                version="2015",
                title="Control of externally provided processes",
                requirement_text="The organization shall ensure ...",
                source_type="standard",
                source_id="ISO 9001",
                clause="8.4",
            ),
        ),
        planned_date=datetime(2026, 11, 1, 9, 0, tzinfo=UTC_PLUS_THREE),
        security_classification_id="internal",
    )
    audit.plan()
    return audit


def _make_closed_audit() -> Audit:
    """Create a CLOSED audit that went through the full lifecycle."""
    audit = _make_planned_audit()
    start = audit.created_at
    audit.issue()
    audit.start(start + timedelta(hours=1))
    audit.attach_report(AuditReportRef("RPT-1", "1.0"))
    audit.complete(start + timedelta(hours=2))
    audit.approve_report("qa-manager", start + timedelta(hours=3))
    audit.close(AuditClosureGate(), start + timedelta(hours=4))
    return audit


def _make_reopened_audit() -> Audit:
    """Create a REOPENED audit."""
    audit = _make_closed_audit()
    audit.reopen("New evidence received", audit.created_at + timedelta(hours=5))
    return audit


def _make_deferred_audit() -> Audit:
    """Create a DEFERRED audit."""
    audit = _make_planned_audit()
    audit.defer("Auditee unavailable")
    return audit


def _make_cancelled_audit() -> Audit:
    """Create a CANCELLED audit."""
    audit = _make_planned_audit()
    audit.cancel("Scope merged into another audit")
    return audit


AUDIT_FACTORIES: dict[str, Callable[[], Audit]] = {
    "draft": _make_draft_audit,
    "planned": _make_planned_audit,
    "closed": _make_closed_audit,
    "reopened": _make_reopened_audit,
    "deferred": _make_deferred_audit,
    "cancelled": _make_cancelled_audit,
}


@pytest.fixture
def repository(tmp_path: Path) -> JsonAuditRepository:
    """Return a repository backed by an isolated temporary directory."""
    return JsonAuditRepository(tmp_path / "data")


# ---------------------------------------------------------------------------
# Initialization, paths and file creation
# ---------------------------------------------------------------------------


def test_repository_implements_audit_repository_contract(
    repository: JsonAuditRepository,
) -> None:
    assert isinstance(repository, AuditRepository)


def test_init_creates_missing_directory_and_empty_data_file(tmp_path: Path) -> None:
    data_dir = tmp_path / "nested" / "storage"

    repository = JsonAuditRepository(data_dir)

    assert data_dir.is_dir()
    assert repository.file_path == data_dir / DEFAULT_FILE_NAME
    assert _read_document(repository) == {
        "schema_version": SCHEMA_VERSION,
        "audits": {},
    }


def test_default_data_directory_is_data_under_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    repository = JsonAuditRepository()

    assert repository.file_path == Path("data") / DEFAULT_FILE_NAME
    assert (tmp_path / "data" / DEFAULT_FILE_NAME).is_file()


def test_custom_file_name_is_used(tmp_path: Path) -> None:
    repository = JsonAuditRepository(tmp_path, file_name="custom.json")

    assert repository.file_path == tmp_path / "custom.json"
    assert repository.file_path.is_file()


def test_init_does_not_overwrite_existing_data(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)

    reopened_repository = JsonAuditRepository(repository.data_dir)

    assert reopened_repository.get_by_id(_uuid(audit)) == audit


@pytest.mark.parametrize("file_name", ["", "nested/audits.json", "../audits.json"])
def test_init_rejects_invalid_file_name(tmp_path: Path, file_name: str) -> None:
    with pytest.raises(ValueError, match="file_name"):
        JsonAuditRepository(tmp_path, file_name=file_name)


def test_init_rejects_negative_lock_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="lock_timeout"):
        JsonAuditRepository(tmp_path, lock_timeout=-1)


def test_init_raises_storage_error_when_directory_cannot_be_created(
    tmp_path: Path,
) -> None:
    blocking_file = tmp_path / "not-a-directory"
    blocking_file.write_text("occupied", encoding="utf-8")

    with pytest.raises(StorageError, match="storage directory"):
        JsonAuditRepository(blocking_file)


# ---------------------------------------------------------------------------
# save & get_by_id
# ---------------------------------------------------------------------------


def test_save_new_audit_and_get_by_id(repository: JsonAuditRepository) -> None:
    audit = _make_draft_audit()

    repository.save(audit)
    loaded = repository.get_by_id(_uuid(audit))

    assert loaded is not None
    assert loaded == audit
    assert loaded is not audit


@pytest.mark.parametrize("state", list(AUDIT_FACTORIES))
def test_round_trip_preserves_complete_state(
    repository: JsonAuditRepository,
    state: str,
) -> None:
    audit = AUDIT_FACTORIES[state]()

    repository.save(audit)
    loaded = repository.get_by_id(_uuid(audit))

    assert loaded == audit


def test_round_trip_restores_strong_domain_types(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_closed_audit()
    repository.save(audit)

    loaded = repository.get_by_id(_uuid(audit))

    assert loaded is not None
    assert loaded.status is AuditStatus.CLOSED
    assert isinstance(loaded.audit_type, AuditTypeRef)
    assert all(isinstance(item, AuditObjectRef) for item in loaded.audit_objects)
    assert loaded.lead_auditor == "auditor-1"
    assert loaded.report_approved
    assert loaded.created_at.tzinfo is not None
    assert loaded.created_at.utcoffset() == timedelta(0)
    assert loaded.planned_date == datetime(2026, 11, 1, 6, 0, tzinfo=UTC)


def test_loaded_audit_remains_mutation_protected(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)

    loaded = repository.get_by_id(_uuid(audit))

    assert loaded is not None
    with pytest.raises(AttributeError):
        loaded.title = "Direct assignment"


def test_loaded_audit_supports_further_domain_transitions(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_planned_audit()
    repository.save(audit)

    loaded = repository.get_by_id(_uuid(audit))
    assert loaded is not None
    loaded.issue()
    repository.save(loaded)

    reloaded = repository.get_by_id(_uuid(audit))
    assert reloaded is not None
    assert reloaded.status is AuditStatus.ISSUED


def test_json_representation_uses_utc_strings_and_uuid_keys(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_closed_audit()
    repository.save(audit)

    document = _read_document(repository)
    record = document["audits"][audit.id]

    assert document["schema_version"] == SCHEMA_VERSION
    assert str(UUID(record["id"])) == audit.id
    assert record["status"] == "closed"
    assert record["created_at"] == audit.created_at.isoformat()
    assert record["created_at"].endswith("+00:00")
    assert record["planned_date"] == "2026-11-01T06:00:00+00:00"
    assert record["report_approval"]["approved_at"].endswith("+00:00")


def test_serialized_record_covers_every_audit_field(
    repository: JsonAuditRepository,
) -> None:
    """Guard against model drift: a new Audit field must be serialized too."""
    audit = _make_draft_audit()
    repository.save(audit)

    record = _read_document(repository)["audits"][audit.id]
    model_fields = {item.name for item in fields(Audit)} - {"_initialized"}

    assert set(record) == model_fields


def test_non_ascii_text_is_stored_readably(repository: JsonAuditRepository) -> None:
    audit = _make_planned_audit()
    repository.save(audit)

    raw_text = repository.file_path.read_text(encoding="utf-8")

    assert "מבדק פנימי ISO 9001" in raw_text


def test_data_persists_across_repository_instances(tmp_path: Path) -> None:
    audit = _make_closed_audit()
    JsonAuditRepository(tmp_path).save(audit)

    assert JsonAuditRepository(tmp_path).get_by_id(_uuid(audit)) == audit


def test_save_rejects_non_audit_objects(repository: JsonAuditRepository) -> None:
    with pytest.raises(TypeError):
        repository.save({"title": "not an audit"})  # type: ignore[arg-type]


def test_save_validates_audit_before_persisting(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    object.__setattr__(audit, "title", "")

    with pytest.raises(ValueError, match="title"):
        repository.save(audit)

    assert repository.list_all() == []


def test_get_by_id_rejects_non_uuid_identifier(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)

    with pytest.raises(TypeError):
        repository.get_by_id(audit.id)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Updating an existing audit
# ---------------------------------------------------------------------------


def test_save_existing_audit_updates_instead_of_duplicating(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)

    audit.set_title("Updated title")
    audit.set_scope("Updated scope")
    repository.save(audit)

    loaded = repository.get_by_id(_uuid(audit))
    assert loaded is not None
    assert loaded.title == "Updated title"
    assert loaded.scope == "Updated scope"
    assert len(repository.list_all()) == 1


def test_save_persists_lifecycle_transitions(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_planned_audit()
    repository.save(audit)

    audit.issue()
    audit.start(audit.created_at + timedelta(minutes=30))
    repository.save(audit)

    loaded = repository.get_by_id(_uuid(audit))
    assert loaded is not None
    assert loaded.status is AuditStatus.IN_PROGRESS
    assert loaded.started_at == audit.started_at


def test_changes_to_loaded_audit_are_not_persisted_without_save(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)

    loaded = repository.get_by_id(_uuid(audit))
    assert loaded is not None
    loaded.set_title("Unsaved change")

    reloaded = repository.get_by_id(_uuid(audit))
    assert reloaded is not None
    assert reloaded.title == "Draft audit"


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------


def test_list_all_returns_empty_list_for_new_storage(
    repository: JsonAuditRepository,
) -> None:
    assert repository.list_all() == []


def test_list_all_returns_every_saved_audit(repository: JsonAuditRepository) -> None:
    audits = [factory() for factory in AUDIT_FACTORIES.values()]
    for audit in audits:
        repository.save(audit)

    loaded = repository.list_all()

    assert sorted(loaded, key=lambda audit: audit.id) == sorted(
        audits,
        key=lambda audit: audit.id,
    )


def test_list_all_does_not_require_a_specific_order(
    repository: JsonAuditRepository,
) -> None:
    audits = [Audit(title=f"Audit {index}") for index in range(5)]
    for audit in reversed(audits):
        repository.save(audit)

    loaded = repository.list_all()

    assert {audit.id for audit in loaded} == {audit.id for audit in audits}


def test_list_all_returns_independent_list(repository: JsonAuditRepository) -> None:
    repository.save(_make_draft_audit())

    snapshot = repository.list_all()
    snapshot.clear()

    assert len(repository.list_all()) == 1


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_removes_audit(repository: JsonAuditRepository) -> None:
    kept = _make_draft_audit()
    removed = _make_planned_audit()
    repository.save(kept)
    repository.save(removed)

    repository.delete(_uuid(removed))

    assert repository.get_by_id(_uuid(removed)) is None
    assert repository.list_all() == [kept]
    assert removed.id not in _read_document(repository)["audits"]


def test_delete_is_persisted_for_new_repository_instances(tmp_path: Path) -> None:
    audit = _make_draft_audit()
    JsonAuditRepository(tmp_path).save(audit)

    JsonAuditRepository(tmp_path).delete(_uuid(audit))

    assert JsonAuditRepository(tmp_path).get_by_id(_uuid(audit)) is None


# ---------------------------------------------------------------------------
# Edge cases: missing identifiers
# ---------------------------------------------------------------------------


def test_get_by_id_returns_none_for_unknown_id(
    repository: JsonAuditRepository,
) -> None:
    """The AuditRepository contract returns None for a missing audit."""
    repository.save(_make_draft_audit())

    assert repository.get_by_id(uuid4()) is None


def test_delete_unknown_id_raises_not_found_error(
    repository: JsonAuditRepository,
) -> None:
    missing_id = uuid4()

    with pytest.raises(NotFoundError) as exc_info:
        repository.delete(missing_id)

    assert exc_info.value.item_id == missing_id
    assert exc_info.value.entity_name == "Audit"
    assert str(missing_id) in str(exc_info.value)


def test_delete_same_id_twice_raises_not_found_error(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)
    repository.delete(_uuid(audit))

    with pytest.raises(NotFoundError):
        repository.delete(_uuid(audit))


def test_not_found_error_is_a_storage_error(repository: JsonAuditRepository) -> None:
    with pytest.raises(StorageError):
        repository.delete(uuid4())


def test_missing_data_file_raises_storage_error(
    repository: JsonAuditRepository,
) -> None:
    repository.file_path.unlink()

    with pytest.raises(StorageError, match="missing"):
        repository.list_all()

    with pytest.raises(StorageError, match="missing"):
        repository.save(_make_draft_audit())


# ---------------------------------------------------------------------------
# Error handling: corrupted or unreadable storage
# ---------------------------------------------------------------------------


def test_invalid_json_raises_storage_error(repository: JsonAuditRepository) -> None:
    repository.file_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(StorageError, match="valid JSON"):
        repository.list_all()
    with pytest.raises(StorageError):
        repository.get_by_id(uuid4())
    with pytest.raises(StorageError):
        repository.save(_make_draft_audit())


@pytest.mark.parametrize(
    "document",
    [
        [],
        {"audits": {}},
        {"schema_version": 999, "audits": {}},
        {"schema_version": True, "audits": {}},
        {"schema_version": SCHEMA_VERSION, "audits": []},
        {"schema_version": SCHEMA_VERSION, "audits": {"some-id": "not-an-object"}},
    ],
    ids=[
        "top-level-list",
        "missing-schema-version",
        "unsupported-schema-version",
        "boolean-schema-version",
        "audits-not-object",
        "record-not-object",
    ],
)
def test_invalid_document_structure_raises_storage_error(
    repository: JsonAuditRepository,
    document: object,
) -> None:
    _write_document(repository, document)

    with pytest.raises(StorageError):
        repository.list_all()


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("status", "not-a-status"),
        ("created_at", "2026-01-01T00:00:00"),
        ("created_at", "not-a-date"),
        ("title", ""),
        ("title", 42),
        ("team", "not-a-list"),
        ("status", "closed"),
    ],
    ids=[
        "unknown-status",
        "naive-datetime",
        "unparseable-datetime",
        "empty-title",
        "non-string-title",
        "team-not-list",
        "violated-domain-invariant",
    ],
)
def test_invalid_stored_record_raises_storage_error(
    repository: JsonAuditRepository,
    field_name: str,
    bad_value: object,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)
    document = _read_document(repository)
    document["audits"][audit.id][field_name] = bad_value
    _write_document(repository, document)

    with pytest.raises(StorageError, match="invalid"):
        repository.get_by_id(_uuid(audit))


def test_record_with_missing_field_raises_storage_error(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)
    document = _read_document(repository)
    del document["audits"][audit.id]["scope"]
    _write_document(repository, document)

    with pytest.raises(StorageError, match="scope"):
        repository.get_by_id(_uuid(audit))


def test_record_stored_under_wrong_key_raises_storage_error(
    repository: JsonAuditRepository,
) -> None:
    audit = _make_draft_audit()
    repository.save(audit)
    other_id = uuid4()
    document = _read_document(repository)
    document["audits"][str(other_id)] = document["audits"].pop(audit.id)
    _write_document(repository, document)

    with pytest.raises(StorageError, match="mismatching id"):
        repository.get_by_id(other_id)


def test_unreadable_data_file_raises_storage_error(tmp_path: Path) -> None:
    repository = JsonAuditRepository(tmp_path)
    repository.file_path.unlink()
    repository.file_path.mkdir()

    with pytest.raises(StorageError, match="Cannot read"):
        repository.list_all()


def test_failed_write_raises_storage_error_and_keeps_previous_data(
    repository: JsonAuditRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = _make_draft_audit()
    repository.save(existing)

    def failing_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated disk failure")

    monkeypatch.setattr("audit_sys.storage.json_storage.os.replace", failing_replace)

    with pytest.raises(StorageError, match="Cannot write"):
        repository.save(_make_planned_audit())

    monkeypatch.undo()
    assert repository.list_all() == [existing]
    assert list(repository.data_dir.glob("*.tmp")) == []


# ---------------------------------------------------------------------------
# Locking and concurrency
# ---------------------------------------------------------------------------


def test_lock_timeout_raises_storage_error(tmp_path: Path) -> None:
    repository = JsonAuditRepository(tmp_path, lock_timeout=0.05)

    with FileLock(repository.lock_path), pytest.raises(StorageError, match="lock"):
        repository.list_all()


def test_lock_is_released_after_each_operation(tmp_path: Path) -> None:
    repository = JsonAuditRepository(tmp_path)
    repository.save(_make_draft_audit())

    competing_lock = FileLock(repository.lock_path, timeout=0.05)
    with competing_lock:
        assert competing_lock.is_locked


def test_lock_is_released_after_failed_operation(tmp_path: Path) -> None:
    repository = JsonAuditRepository(tmp_path)
    with pytest.raises(NotFoundError):
        repository.delete(uuid4())

    competing_lock = FileLock(repository.lock_path, timeout=0.05)
    with competing_lock:
        assert competing_lock.is_locked


def test_concurrent_saves_do_not_lose_updates(tmp_path: Path) -> None:
    audits = [Audit(title=f"Concurrent audit {index}") for index in range(30)]

    def save_with_own_instance(audit: Audit) -> None:
        JsonAuditRepository(tmp_path).save(audit)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(save_with_own_instance, audits))

    stored_ids = {audit.id for audit in JsonAuditRepository(tmp_path).list_all()}
    assert stored_ids == {audit.id for audit in audits}
