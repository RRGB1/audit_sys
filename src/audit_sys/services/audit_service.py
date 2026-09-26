"""Application service for the Audit aggregate (MVP use cases).

``AuditService`` is the entry point that Interfaces (CLI, API, UI) call to
create, read, list and delete audits. It orchestrates the use case and
depends only on the abstract :class:`~audit_sys.storage.base.AuditRepository`
port, which is injected through the constructor. The service never imports a
concrete adapter (JSON, PostgreSQL, in-memory); the Composition Root decides
which adapter to inject::

    from audit_sys.services.audit_service import AuditService
    from audit_sys.storage.json_storage import JsonAuditRepository

    service = AuditService(JsonAuditRepository())

Responsibilities are split as follows:
    - The domain model (``Audit``) owns identity (UUID4), UTC timestamps and
      all local invariants.
    - The service validates use-case input that the domain does not see
      (identifier types, status filters), translates domain validation
      failures into :class:`DomainValidationError`, and applies read-side
      concerns such as filtering and deterministic ordering.
    - Storage failures are raised by the repository as
      :class:`~audit_sys.storage.base.StorageError` (or its subclass
      :class:`~audit_sys.storage.base.NotFoundError`) and propagate unchanged,
      so callers can map them consistently.

Out of scope for this MVP service, as planned in ARCHITECTURE.md: ActorContext
and authorization, Unit of Work, Audit Trail and Domain Events. They can be
added to the constructor and use cases without changing the public methods'
return types.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from audit_sys.models.core import (
    Audit,
    AuditCriterionSnapshot,
    AuditObjectRef,
    AuditStatus,
    AuditTeamMember,
    AuditTypeRef,
)
from audit_sys.storage.base import AuditRepository, NotFoundError

__all__ = [
    "AuditService",
    "AuditServiceError",
    "DomainValidationError",
]

_ENTITY_NAME = "Audit"


class AuditServiceError(Exception):
    """Base class for errors raised by the Audit application service."""


class DomainValidationError(AuditServiceError, ValueError):
    """Raised when use-case input is invalid.

    Covers both input rejected by the service itself (for example an unknown
    status filter or a non-UUID identifier) and input rejected by the domain
    model's invariants. The original domain exception, when there is one, is
    available as ``__cause__``.

    Also inherits from ``ValueError`` so generic callers can catch it
    idiomatically. The Interfaces layer maps it to HTTP 422 (ARCHITECTURE.md
    §53).
    """


def _require_uuid(audit_id: UUID) -> UUID:
    """Return ``audit_id`` if it is a ``uuid.UUID``; otherwise fail clearly."""
    if not isinstance(audit_id, UUID):
        raise DomainValidationError(
            f"audit_id must be a uuid.UUID, got {type(audit_id).__name__}."
        )
    return audit_id


def _parse_status(status: str | AuditStatus) -> AuditStatus:
    """Convert a status filter into an ``AuditStatus``.

    Accepts an ``AuditStatus`` member or its string value. String matching is
    case-insensitive and ignores surrounding whitespace, so ``"planned"``,
    ``"PLANNED"`` and ``" Planned "`` are equivalent.
    """
    if isinstance(status, AuditStatus):
        return status

    if not isinstance(status, str):
        raise DomainValidationError(
            f"status must be a string or AuditStatus, got {type(status).__name__}."
        )

    normalized = status.strip().lower()
    try:
        return AuditStatus(normalized)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in AuditStatus)
        raise DomainValidationError(
            f"Unknown audit status '{status}'. Allowed values: {allowed}."
        ) from exc


class AuditService:
    """Use cases for creating, reading, listing and deleting audits.

    The service is stateless apart from the injected repository, so a single
    instance can be shared by the whole application.
    """

    def __init__(self, storage: AuditRepository) -> None:
        """Create the service around an injected repository port.

        Args:
            storage: Repository implementation supplied by the composition root.

        Notes:
            Runtime ``isinstance`` checks are intentionally avoided here. The
            dependency is governed by the typed repository contract, keeping the
            service compatible with future Protocol-based ports and test doubles.
        """
        self._storage = storage

    def create_audit(
        self,
        title: str,
        *,
        objective: str = "",
        scope: str = "",
        audit_type: AuditTypeRef | None = None,
        audit_programme_id: str | None = None,
        audit_objects: Iterable[AuditObjectRef] = (),
        team: Iterable[AuditTeamMember] = (),
        criteria: Iterable[AuditCriterionSnapshot] = (),
        planned_date: datetime | None = None,
        security_classification_id: str | None = None,
    ) -> Audit:
        """Create a new DRAFT audit, persist it and return it.

        The domain model generates the UUID4 identifier and the UTC
        ``created_at`` timestamp, normalizes text fields and ``planned_date``
        to UTC, and enforces its invariants. The audit is persisted only if it
        was created successfully.

        Args:
            title: Mandatory, non-empty audit title.
            objective: Optional audit objective.
            scope: Optional audit scope.
            audit_type: Reference to the Audit Type master data.
            audit_programme_id: Optional Audit Programme reference.
            audit_objects: Auditable-object references; no duplicates.
            team: Audit team members; at most one Lead Auditor.
            criteria: Versioned criterion snapshots; one per criterion id.
            planned_date: Timezone-aware planned date/time.
            security_classification_id: Optional classification reference.

        Returns:
            The newly created and persisted ``Audit``.

        Raises:
            DomainValidationError: If any input violates the domain rules.
            StorageError: If the repository fails to persist the audit.
        """
        try:
            audit = Audit(
                title=title,
                objective=objective,
                scope=scope,
                audit_type=audit_type,
                audit_programme_id=audit_programme_id,
                audit_objects=tuple(audit_objects),
                team=tuple(team),
                criteria=tuple(criteria),
                planned_date=planned_date,
                security_classification_id=security_classification_id,
            )
        except (TypeError, ValueError) as exc:
            raise DomainValidationError(f"Cannot create audit: {exc}") from exc

        self._storage.save(audit)
        return audit

    def get_audit(self, audit_id: UUID) -> Audit:
        """Return the audit with ``audit_id``.

        Args:
            audit_id: UUID of the requested audit.

        Returns:
            The stored ``Audit``.

        Raises:
            DomainValidationError: If ``audit_id`` is not a ``uuid.UUID``.
            NotFoundError: If no audit with ``audit_id`` exists.
            StorageError: If the repository fails to read the audit.
        """
        valid_id = _require_uuid(audit_id)

        audit = self._storage.get_by_id(valid_id)
        if audit is None:
            raise NotFoundError(_ENTITY_NAME, valid_id)
        return audit

    def list_audits(
        self,
        status: str | AuditStatus | None = None,
    ) -> list[Audit]:
        """Return all audits, optionally filtered by lifecycle status.

        The result is ordered by ``created_at`` and then ``id``, regardless of
        the order returned by the repository.

        Args:
            status: Optional status filter, as an ``AuditStatus`` member or its
                value (case-insensitive), for example ``"planned"``.

        Returns:
            A new list of matching audits; empty if none match.

        Raises:
            DomainValidationError: If ``status`` is not a known status.
            StorageError: If the repository fails to read the audits.
        """
        wanted_status = None if status is None else _parse_status(status)

        audits = self._storage.list_all()
        if wanted_status is not None:
            audits = [audit for audit in audits if audit.status is wanted_status]

        return sorted(audits, key=lambda audit: (audit.created_at, audit.id))

    def delete_audit(self, audit_id: UUID) -> None:
        """Delete the audit with ``audit_id``.

        This is a physical delete. A retention policy for audits is not yet
        defined in ARCHITECTURE.md; when one is decided, this method is the
        single place to enforce it.

        Args:
            audit_id: UUID of the audit to delete.

        Raises:
            DomainValidationError: If ``audit_id`` is not a ``uuid.UUID``.
            NotFoundError: If no audit with ``audit_id`` exists.
            StorageError: If the repository fails to delete the audit.
        """
        self._storage.delete(_require_uuid(audit_id))
