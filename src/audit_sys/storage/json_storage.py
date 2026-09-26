"""JSON file storage adapter for the Audit aggregate (MVP).

This module implements :class:`~audit_sys.storage.base.AuditRepository` on top
of a single local JSON file. It is intended for the MVP and for local
development; the Application layer depends only on the abstract repository
contract, so this adapter can later be replaced by a database adapter without
changing callers.

File layout::

    <data_dir>/
        audits.json         # the data document
        audits.json.lock    # inter-process lock file managed by ``filelock``

Document format::

    {
        "schema_version": 1,
        "audits": {
            "<audit id>": { ...serialized Audit... }
        }
    }

Concurrency and durability guarantees:
    - Every read and every write is performed while holding a ``FileLock``.
    - ``save`` and ``delete`` hold the lock for the whole read-modify-write
      cycle, so concurrent writers (threads or processes) cannot lose each
      other's updates.
    - Writes are atomic: the new document is written to a temporary file in
      the same directory, flushed and fsynced, and then moved over the data
      file with ``os.replace``. A crash mid-write leaves the previous document
      intact.

Serialization rules:
    - Datetimes are stored as ISO 8601 strings normalized to UTC
      (``"2026-11-01T06:00:00+00:00"``) and must be timezone-aware on load.
    - Enums are stored by value; ``Audit.id`` is stored as its canonical UUID4
      string. Public methods accept ``uuid.UUID`` and convert with ``str()``.
    - On load, an ``Audit`` is rebuilt through its constructor, its
      lifecycle state is restored explicitly, and ``Audit.validate()`` is
      called so every domain invariant is re-checked. Invalid stored data is
      reported as :class:`~audit_sys.storage.base.StorageError`.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast
from uuid import UUID

from filelock import FileLock, Timeout

from audit_sys.models.core import (
    Audit,
    AuditCriterionSnapshot,
    AuditObjectKind,
    AuditObjectRef,
    AuditReportApproval,
    AuditReportRef,
    AuditStatus,
    AuditTeamMember,
    AuditTeamRole,
    AuditTypeRef,
)
from audit_sys.storage.base import AuditRepository, NotFoundError, StorageError

__all__ = [
    "DEFAULT_DATA_DIR",
    "DEFAULT_FILE_NAME",
    "DEFAULT_LOCK_TIMEOUT_SECONDS",
    "SCHEMA_VERSION",
    "JsonAuditRepository",
]

DEFAULT_DATA_DIR: Final[Path] = Path("data")
"""Default storage directory, resolved relative to the current working dir."""

DEFAULT_FILE_NAME: Final[str] = "audits.json"
"""Default name of the JSON data file inside the storage directory."""

DEFAULT_LOCK_TIMEOUT_SECONDS: Final[float] = 10.0
"""Default maximum time to wait for the file lock before failing."""

SCHEMA_VERSION: Final[int] = 1
"""Version of the on-disk document format written by this adapter."""

_ENTITY_NAME: Final[str] = "Audit"

type JsonObject = dict[str, object]
"""A decoded JSON object with string keys."""


# ---------------------------------------------------------------------------
# Serialization: domain -> JSON
# ---------------------------------------------------------------------------


def _datetime_to_json(value: datetime | None) -> str | None:
    """Serialize a timezone-aware datetime as an ISO 8601 UTC string."""
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise StorageError("Cannot serialize a naive datetime.")
    return value.astimezone(UTC).isoformat()


def _report_to_json(report: AuditReportRef | None) -> JsonObject | None:
    """Serialize an optional report reference."""
    if report is None:
        return None
    return {"report_id": report.report_id, "version": report.version}


def _approval_to_json(approval: AuditReportApproval | None) -> JsonObject | None:
    """Serialize an optional report approval record."""
    if approval is None:
        return None
    return {
        "report": _report_to_json(approval.report),
        "approved_by": approval.approved_by,
        "approved_at": _datetime_to_json(approval.approved_at),
    }


def _criterion_to_json(criterion: AuditCriterionSnapshot) -> JsonObject:
    """Serialize a criterion snapshot."""
    return {
        "criterion_id": criterion.criterion_id,
        "version": criterion.version,
        "title": criterion.title,
        "requirement_text": criterion.requirement_text,
        "source_type": criterion.source_type,
        "source_id": criterion.source_id,
        "clause": criterion.clause,
    }


def _audit_to_json(audit: Audit) -> JsonObject:
    """Serialize the complete state of an ``Audit`` aggregate."""
    return {
        # Identity and lifecycle
        "id": audit.id,
        "created_at": _datetime_to_json(audit.created_at),
        "status": audit.status.value,
        # Planning data
        "title": audit.title,
        "objective": audit.objective,
        "scope": audit.scope,
        "audit_type": (
            None
            if audit.audit_type is None
            else {"audit_type_id": audit.audit_type.audit_type_id}
        ),
        "audit_programme_id": audit.audit_programme_id,
        "audit_objects": [
            {"kind": item.kind.value, "object_id": item.object_id}
            for item in audit.audit_objects
        ],
        "team": [
            {"auditor_id": member.auditor_id, "role": member.role.value}
            for member in audit.team
        ],
        "criteria": [_criterion_to_json(item) for item in audit.criteria],
        "planned_date": _datetime_to_json(audit.planned_date),
        "security_classification_id": audit.security_classification_id,
        # Execution, report and closure
        "started_at": _datetime_to_json(audit.started_at),
        "completed_at": _datetime_to_json(audit.completed_at),
        "closed_at": _datetime_to_json(audit.closed_at),
        "report": _report_to_json(audit.report),
        "report_approval": _approval_to_json(audit.report_approval),
        # Deferral, cancellation and reopening
        "deferred_at": _datetime_to_json(audit.deferred_at),
        "deferred_from_status": (
            None
            if audit.deferred_from_status is None
            else audit.deferred_from_status.value
        ),
        "last_defer_reason": audit.last_defer_reason,
        "cancelled_at": _datetime_to_json(audit.cancelled_at),
        "last_cancel_reason": audit.last_cancel_reason,
        "reopened_at": _datetime_to_json(audit.reopened_at),
        "last_reopen_reason": audit.last_reopen_reason,
    }


# ---------------------------------------------------------------------------
# Deserialization: JSON -> domain
#
# The readers raise KeyError / TypeError / ValueError on malformed input; the
# repository converts those into StorageError at the storage boundary.
# ---------------------------------------------------------------------------


def _read_value(data: Mapping[str, object], key: str) -> object:
    """Return a mandatory field value from a decoded JSON object."""
    if key not in data:
        raise KeyError(f"missing field '{key}'")
    return data[key]


def _read_str(data: Mapping[str, object], key: str) -> str:
    """Read a mandatory string field."""
    value = _read_value(data, key)
    if not isinstance(value, str):
        raise TypeError(f"field '{key}' must be a string")
    return value


def _read_optional_str(data: Mapping[str, object], key: str) -> str | None:
    """Read a string field that may be null."""
    if _read_value(data, key) is None:
        return None
    return _read_str(data, key)


def _parse_datetime(value: str, key: str) -> datetime:
    """Parse an ISO 8601 timestamp, requiring timezone info, into UTC."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"field '{key}' must be a timezone-aware timestamp")
    return parsed.astimezone(UTC)


def _read_datetime(data: Mapping[str, object], key: str) -> datetime:
    """Read a mandatory timestamp field as a UTC datetime."""
    return _parse_datetime(_read_str(data, key), key)


def _read_optional_datetime(data: Mapping[str, object], key: str) -> datetime | None:
    """Read a timestamp field that may be null."""
    value = _read_optional_str(data, key)
    if value is None:
        return None
    return _parse_datetime(value, key)


def _read_optional_object(
    data: Mapping[str, object],
    key: str,
) -> Mapping[str, object] | None:
    """Read a JSON object field that may be null."""
    value = _read_value(data, key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError(f"field '{key}' must be an object or null")
    return cast(dict[str, object], value)


def _read_object(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    """Read a mandatory JSON object field."""
    value = _read_optional_object(data, key)
    if value is None:
        raise TypeError(f"field '{key}' must be an object")
    return value


def _read_object_list(
    data: Mapping[str, object],
    key: str,
) -> list[Mapping[str, object]]:
    """Read a mandatory field holding a list of JSON objects."""
    value = _read_value(data, key)
    if not isinstance(value, list):
        raise TypeError(f"field '{key}' must be a list")
    objects: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise TypeError(f"every item of '{key}' must be an object")
        objects.append(cast(dict[str, object], item))
    return objects


def _report_from_json(data: Mapping[str, object]) -> AuditReportRef:
    """Rebuild a report reference."""
    return AuditReportRef(
        report_id=_read_str(data, "report_id"),
        version=_read_str(data, "version"),
    )


def _approval_from_json(data: Mapping[str, object]) -> AuditReportApproval:
    """Rebuild a report approval record."""
    return AuditReportApproval(
        report=_report_from_json(_read_object(data, "report")),
        approved_by=_read_str(data, "approved_by"),
        approved_at=_read_datetime(data, "approved_at"),
    )


def _criterion_from_json(data: Mapping[str, object]) -> AuditCriterionSnapshot:
    """Rebuild a criterion snapshot."""
    return AuditCriterionSnapshot(
        criterion_id=_read_str(data, "criterion_id"),
        version=_read_str(data, "version"),
        title=_read_str(data, "title"),
        requirement_text=_read_str(data, "requirement_text"),
        source_type=_read_str(data, "source_type"),
        source_id=_read_str(data, "source_id"),
        clause=_read_optional_str(data, "clause"),
    )


def _audit_from_json(data: Mapping[str, object]) -> Audit:
    """Rehydrate an ``Audit`` aggregate and re-validate its invariants.

    The constructor only accepts planning data and always creates a new DRAFT
    audit with a fresh id. The persisted identity and lifecycle state are
    therefore restored afterwards with ``object.__setattr__`` (bypassing the
    aggregate's mutation guard), and ``validate()`` is called on the complete
    state before the object is returned.
    """
    audit_type_data = _read_optional_object(data, "audit_type")

    audit = Audit(
        title=_read_str(data, "title"),
        objective=_read_str(data, "objective"),
        scope=_read_str(data, "scope"),
        audit_type=(
            None
            if audit_type_data is None
            else AuditTypeRef(_read_str(audit_type_data, "audit_type_id"))
        ),
        audit_programme_id=_read_optional_str(data, "audit_programme_id"),
        audit_objects=tuple(
            AuditObjectRef(
                kind=AuditObjectKind(_read_str(item, "kind")),
                object_id=_read_str(item, "object_id"),
            )
            for item in _read_object_list(data, "audit_objects")
        ),
        team=tuple(
            AuditTeamMember(
                auditor_id=_read_str(item, "auditor_id"),
                role=AuditTeamRole(_read_str(item, "role")),
            )
            for item in _read_object_list(data, "team")
        ),
        criteria=tuple(
            _criterion_from_json(item) for item in _read_object_list(data, "criteria")
        ),
        planned_date=_read_optional_datetime(data, "planned_date"),
        security_classification_id=_read_optional_str(
            data,
            "security_classification_id",
        ),
    )

    report_data = _read_optional_object(data, "report")
    approval_data = _read_optional_object(data, "report_approval")
    deferred_from = _read_optional_str(data, "deferred_from_status")

    restored_state: dict[str, object] = {
        "id": _read_str(data, "id"),
        "created_at": _read_datetime(data, "created_at"),
        "status": AuditStatus(_read_str(data, "status")),
        "started_at": _read_optional_datetime(data, "started_at"),
        "completed_at": _read_optional_datetime(data, "completed_at"),
        "closed_at": _read_optional_datetime(data, "closed_at"),
        "report": None if report_data is None else _report_from_json(report_data),
        "report_approval": (
            None if approval_data is None else _approval_from_json(approval_data)
        ),
        "deferred_at": _read_optional_datetime(data, "deferred_at"),
        "deferred_from_status": (
            None if deferred_from is None else AuditStatus(deferred_from)
        ),
        "last_defer_reason": _read_optional_str(data, "last_defer_reason"),
        "cancelled_at": _read_optional_datetime(data, "cancelled_at"),
        "last_cancel_reason": _read_optional_str(data, "last_cancel_reason"),
        "reopened_at": _read_optional_datetime(data, "reopened_at"),
        "last_reopen_reason": _read_optional_str(data, "last_reopen_reason"),
    }

    for name, value in restored_state.items():
        object.__setattr__(audit, name, value)

    audit.validate()
    return audit


def _to_key(item_id: UUID) -> str:
    """Convert a UUID into the canonical string key used by the domain."""
    if not isinstance(item_id, UUID):
        raise TypeError("item_id must be a uuid.UUID instance.")
    return str(item_id)


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class JsonAuditRepository(AuditRepository):
    """Store ``Audit`` aggregates in a local JSON file.

    Example::

        repository = JsonAuditRepository()            # ./data/audits.json
        repository = JsonAuditRepository("var/data")  # custom directory

        audit = Audit(title="Internal audit")
        repository.save(audit)
        loaded = repository.get_by_id(UUID(audit.id))

    The storage directory and an empty data file are created automatically
    when the repository is constructed. Every operation reads the file from
    disk, so several repository instances (or processes) pointing to the same
    directory always observe each other's committed changes.
    """

    def __init__(
        self,
        data_dir: str | os.PathLike[str] = DEFAULT_DATA_DIR,
        *,
        file_name: str = DEFAULT_FILE_NAME,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    ) -> None:
        """Configure the repository and make sure its storage exists.

        Args:
            data_dir: Directory holding the data file. Relative paths are
                resolved against the current working directory. Defaults to
                ``data``.
            file_name: Name of the JSON data file inside ``data_dir``. Must be
                a plain file name without directory components.
            lock_timeout: Maximum number of seconds to wait for the file lock
                before an operation fails with ``StorageError``.

        Raises:
            ValueError: If ``file_name`` or ``lock_timeout`` is invalid.
            StorageError: If the directory or data file cannot be created, or
                the lock cannot be acquired in time.
        """
        if not file_name or Path(file_name).name != file_name:
            raise ValueError("file_name must be a plain file name.")
        if lock_timeout < 0:
            raise ValueError("lock_timeout cannot be negative.")

        self._data_dir = Path(data_dir)
        self._file_path = self._data_dir / file_name
        self._lock_path = self._data_dir / f"{file_name}.lock"
        self._lock_timeout = lock_timeout
        self._lock = FileLock(str(self._lock_path))

        self._ensure_storage()

    # -- Public properties --------------------------------------------------

    @property
    def data_dir(self) -> Path:
        """Directory that holds the data file and its lock file."""
        return self._data_dir

    @property
    def file_path(self) -> Path:
        """Path of the JSON data file."""
        return self._file_path

    @property
    def lock_path(self) -> Path:
        """Path of the lock file used to synchronize access."""
        return self._lock_path

    # -- AuditRepository contract ------------------------------------------

    def save(self, item: Audit) -> None:
        """Create or replace the stored state of ``item``.

        Raises:
            TypeError: If ``item`` is not an ``Audit``.
            StorageError: If the data file cannot be read or written.
        """
        if not isinstance(item, Audit):
            raise TypeError("item must be an Audit instance.")

        item.validate()
        record = _audit_to_json(item)

        with self._locked():
            records = self._read_records()
            records[item.id] = record
            self._write_records(records)

    def get_by_id(self, item_id: UUID) -> Audit | None:
        """Return the stored ``Audit`` with ``item_id``, or ``None``.

        Each call returns a new, independent ``Audit`` instance; changes to it
        are not persisted until it is passed to ``save``.

        Raises:
            TypeError: If ``item_id`` is not a ``uuid.UUID``.
            StorageError: If the data file or the stored record is invalid.
        """
        key = _to_key(item_id)

        with self._locked():
            records = self._read_records()

        record = records.get(key)
        if record is None:
            return None
        return self._deserialize(key, record)

    def list_all(self) -> list[Audit]:
        """Return all stored audits without guaranteeing a specific order.

        Raises:
            StorageError: If the data file or any stored record is invalid.
        """
        with self._locked():
            records = self._read_records()

        return [self._deserialize(key, record) for key, record in records.items()]

    def delete(self, item_id: UUID) -> None:
        """Delete the stored ``Audit`` with ``item_id``.

        Raises:
            TypeError: If ``item_id`` is not a ``uuid.UUID``.
            NotFoundError: If no audit with ``item_id`` is stored.
            StorageError: If the data file cannot be read or written.
        """
        key = _to_key(item_id)

        with self._locked():
            records = self._read_records()
            if key not in records:
                raise NotFoundError(_ENTITY_NAME, item_id)
            del records[key]
            self._write_records(records)

    # -- Internals -----------------------------------------------------------

    @contextlib.contextmanager
    def _locked(self) -> Iterator[None]:
        """Hold the inter-process file lock for the duration of the block."""
        try:
            self._lock.acquire(timeout=self._lock_timeout)
        except Timeout as exc:
            raise StorageError(
                f"Timed out after {self._lock_timeout} seconds waiting for "
                f"the storage lock '{self._lock_path}'."
            ) from exc
        except OSError as exc:
            raise StorageError(
                f"Cannot acquire the storage lock '{self._lock_path}': {exc}"
            ) from exc

        try:
            yield
        finally:
            self._lock.release()

    def _ensure_storage(self) -> None:
        """Create the storage directory and an empty data file if missing."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(
                f"Cannot create the storage directory '{self._data_dir}': {exc}"
            ) from exc

        with self._locked():
            if not self._file_path.exists():
                self._write_records({})

    def _read_records(self) -> dict[str, JsonObject]:
        """Read and structurally validate the data document.

        Must be called while holding the lock. A missing data file after
        repository initialization is treated as a storage-integrity failure.
        """
        try:
            with self._file_path.open(encoding="utf-8") as file:
                document: object = json.load(file)
        except FileNotFoundError as exc:
            raise StorageError(
                f"Storage file '{self._file_path}' is missing."
            ) from exc
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"Storage file '{self._file_path}' does not contain valid JSON: {exc}"
            ) from exc
        except (OSError, UnicodeDecodeError) as exc:
            raise StorageError(
                f"Cannot read the storage file '{self._file_path}': {exc}"
            ) from exc

        if not isinstance(document, dict):
            raise StorageError(
                f"Storage file '{self._file_path}' must contain a JSON object."
            )

        document_object = cast(dict[str, object], document)

        schema_version = document_object.get("schema_version")
        if type(schema_version) is not int or schema_version != SCHEMA_VERSION:
            raise StorageError(
                f"Unsupported schema_version {schema_version!r} in "
                f"'{self._file_path}'; expected {SCHEMA_VERSION}."
            )

        audits = document_object.get("audits")
        if not isinstance(audits, dict):
            raise StorageError(
                f"Storage file '{self._file_path}' must contain an 'audits' object."
            )

        audits_object = cast(dict[str, object], audits)

        records: dict[str, JsonObject] = {}
        for key, record in audits_object.items():
            if not isinstance(record, dict):
                raise StorageError(
                    f"Stored audit record '{key}' must be a JSON object."
                )
            records[key] = cast(JsonObject, record)
        return records

    def _write_records(self, records: Mapping[str, JsonObject]) -> None:
        """Atomically replace the data document with ``records``.

        Must be called while holding the lock.
        """
        document: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "audits": dict(records),
        }
        payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True)

        temp_path: Path | None = None
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            file_descriptor, temp_name = tempfile.mkstemp(
                dir=self._data_dir,
                prefix=f".{self._file_path.name}.",
                suffix=".tmp",
            )
            temp_path = Path(temp_name)
            with os.fdopen(
                file_descriptor,
                "w",
                encoding="utf-8",
                newline="\n",
            ) as temp_file:
                temp_file.write(payload)
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, self._file_path)
        except OSError as exc:
            if temp_path is not None:
                with contextlib.suppress(OSError):
                    temp_path.unlink(missing_ok=True)
            raise StorageError(
                f"Cannot write the storage file '{self._file_path}': {exc}"
            ) from exc

    def _deserialize(self, key: str, record: Mapping[str, object]) -> Audit:
        """Rebuild an ``Audit`` from a stored record or raise StorageError."""
        try:
            audit = _audit_from_json(record)
        except (KeyError, TypeError, ValueError) as exc:
            raise StorageError(
                f"Stored audit record '{key}' in '{self._file_path}' is invalid: {exc}"
            ) from exc

        if audit.id != key:
            raise StorageError(
                f"Stored audit record '{key}' contains a mismatching id '{audit.id}'."
            )
        return audit
