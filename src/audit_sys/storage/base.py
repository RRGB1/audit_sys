"""Storage abstraction layer for Audit repository contracts.

This module defines the persistence contract used by the Application layer and
implemented by concrete storage adapters such as in-memory, JSON, or PostgreSQL
repositories. It contains interfaces and storage-level exceptions only; no
physical persistence logic belongs here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from audit_sys.models.core import Audit

__all__ = [
    "AuditRepository",
    "NotFoundError",
    "StorageError",
]


class StorageError(Exception):
    """Base exception for failures raised by storage adapters."""


class NotFoundError(StorageError):
    """Raised when an operation requires an entity that does not exist."""

    def __init__(self, entity_name: str, item_id: UUID) -> None:
        """Initialize the error with the missing entity type and identifier."""
        self.entity_name = entity_name
        self.item_id = item_id
        super().__init__(f"{entity_name} with id '{item_id}' was not found.")


class AuditRepository(ABC):
    """Abstract persistence contract for the :class:`Audit` aggregate.

    Concrete adapters must preserve the same externally visible semantics:

    - ``save`` creates a new audit or updates the stored state of an existing
      audit.
    - ``get_by_id`` returns ``None`` when the requested audit does not exist.
    - ``list_all`` returns all persisted audits as a new list.
    - ``delete`` raises :class:`NotFoundError` when the requested audit does not
      exist.
    - backend-specific failures must be exposed as :class:`StorageError` or one
      of its subclasses rather than leaking implementation-specific exceptions
      into the Application layer.

    The current domain model stores ``Audit.id`` as a canonical UUID4 string,
    while this repository contract accepts :class:`UUID` values. Concrete
    adapters are responsible for normalizing identifiers at the storage
    boundary, for example with ``str(item_id)`` when using string keys.

    When an adapter rehydrates an ``Audit`` from persisted data, it must restore
    the complete aggregate state and validate the reconstructed object with
    ``Audit.validate()`` before returning it.
    """

    @abstractmethod
    def save(self, item: Audit) -> None:
        """Persist a new Audit or update an existing Audit.

        Args:
            item: Audit aggregate to persist.

        Raises:
            StorageError: If the persistence operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, item_id: UUID) -> Audit | None:
        """Return an Audit by its identifier.

        Args:
            item_id: UUID of the requested Audit.

        Returns:
            The validated Audit aggregate, or ``None`` when no matching Audit
            exists.

        Raises:
            StorageError: If the read operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Audit]:
        """Return all persisted Audits.

        Returns:
            A new list containing all validated Audit aggregates. The list is
            empty when no Audits are stored. Ordering is not guaranteed by this
            contract.

        Raises:
            StorageError: If the read operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, item_id: UUID) -> None:
        """Delete an Audit by its identifier.

        Args:
            item_id: UUID of the Audit to delete.

        Raises:
            NotFoundError: If no Audit exists with the supplied identifier.
            StorageError: If the delete operation otherwise fails.
        """
        raise NotImplementedError
