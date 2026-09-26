"""FastAPI interface layer for the Audit Management system (MVP).

This module translates HTTP requests into calls on
:class:`~audit_sys.services.audit_service.AuditService` and maps the results
and errors back to HTTP. Following ARCHITECTURE.md §50-§53 it:

- parses and validates request bodies with Pydantic DTOs,
- calls the application service, which owns every business rule,
- maps service and storage errors to HTTP status codes in one place,
- returns response DTOs and never exposes domain entities directly.

The module also acts as the MVP composition root: ``get_audit_service`` is the
only place that chooses the concrete storage adapter. The data directory is
read from the ``AUDIT_SYS_DATA_DIR`` environment variable (default: ``data``).

Run locally::

    uv run uvicorn audit_sys.web.main:app --reload

Interactive API documentation is then available at ``/docs``.

Endpoints are plain ``def`` functions on purpose: the JSON storage performs
blocking file I/O, and FastAPI runs synchronous endpoints in a worker thread
pool so they do not block the event loop.
"""

import logging
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Final, Self
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

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
from audit_sys.services.audit_service import AuditService, DomainValidationError
from audit_sys.storage.base import NotFoundError, StorageError
from audit_sys.storage.json_storage import JsonAuditRepository

__all__ = [
    "DATA_DIR_ENV_VAR",
    "DEFAULT_DATA_DIR",
    "STORAGE_FAILURE_DETAIL",
    "AuditCriterionDTO",
    "AuditObjectRefDTO",
    "AuditReportApprovalDTO",
    "AuditReportRefDTO",
    "AuditResponse",
    "AuditTeamMemberDTO",
    "CreateAuditRequest",
    "app",
    "get_audit_service",
    "get_data_dir",
]

logger = logging.getLogger(__name__)

DATA_DIR_ENV_VAR: Final[str] = "AUDIT_SYS_DATA_DIR"
"""Environment variable that overrides the JSON data directory."""

DEFAULT_DATA_DIR: Final[Path] = Path("data")
"""Data directory used when the environment variable is not set."""

STORAGE_FAILURE_DETAIL: Final[str] = (
    "The operation could not be completed because of a storage failure."
)

_ALLOWED_STATUSES: Final[str] = ", ".join(member.value for member in AuditStatus)


# ---------------------------------------------------------------------------
# DTOs (Pydantic boundary models)
# ---------------------------------------------------------------------------


class AuditObjectRefDTO(BaseModel):
    """Reference to an auditable object."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: AuditObjectKind
    object_id: str = Field(min_length=1)

    def to_domain(self) -> AuditObjectRef:
        """Convert to the domain value object."""
        return AuditObjectRef(kind=self.kind, object_id=self.object_id)

    @classmethod
    def from_domain(cls, value: AuditObjectRef) -> Self:
        """Build the DTO from the domain value object."""
        return cls(kind=value.kind, object_id=value.object_id)


class AuditTeamMemberDTO(BaseModel):
    """Auditor assignment inside an audit team."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    auditor_id: str = Field(min_length=1)
    role: AuditTeamRole = AuditTeamRole.AUDITOR

    def to_domain(self) -> AuditTeamMember:
        """Convert to the domain value object."""
        return AuditTeamMember(auditor_id=self.auditor_id, role=self.role)

    @classmethod
    def from_domain(cls, value: AuditTeamMember) -> Self:
        """Build the DTO from the domain value object."""
        return cls(auditor_id=value.auditor_id, role=value.role)


class AuditCriterionDTO(BaseModel):
    """Versioned snapshot of an audit criterion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    criterion_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    requirement_text: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    clause: str | None = None

    def to_domain(self) -> AuditCriterionSnapshot:
        """Convert to the domain value object."""
        return AuditCriterionSnapshot(
            criterion_id=self.criterion_id,
            version=self.version,
            title=self.title,
            requirement_text=self.requirement_text,
            source_type=self.source_type,
            source_id=self.source_id,
            clause=self.clause,
        )

    @classmethod
    def from_domain(cls, value: AuditCriterionSnapshot) -> Self:
        """Build the DTO from the domain value object."""
        return cls(
            criterion_id=value.criterion_id,
            version=value.version,
            title=value.title,
            requirement_text=value.requirement_text,
            source_type=value.source_type,
            source_id=value.source_id,
            clause=value.clause,
        )


class AuditReportRefDTO(BaseModel):
    """Reference to a versioned audit report (response only)."""

    model_config = ConfigDict(frozen=True)

    report_id: str
    version: str

    @classmethod
    def from_domain(cls, value: AuditReportRef) -> Self:
        """Build the DTO from the domain value object."""
        return cls(report_id=value.report_id, version=value.version)


class AuditReportApprovalDTO(BaseModel):
    """Approval record of the attached report version (response only)."""

    model_config = ConfigDict(frozen=True)

    report: AuditReportRefDTO
    approved_by: str
    approved_at: datetime

    @classmethod
    def from_domain(cls, value: AuditReportApproval) -> Self:
        """Build the DTO from the domain value object."""
        return cls(
            report=AuditReportRefDTO.from_domain(value.report),
            approved_by=value.approved_by,
            approved_at=value.approved_at,
        )


class CreateAuditRequest(BaseModel):
    """Request body for ``POST /audits``.

    The DTO validates format and types. Business invariants (for example a
    single Lead Auditor or unique audit objects) are enforced by the domain
    model and reported as HTTP 422.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "title": "ISO 9001 internal audit",
                    "scope": "Production line A",
                    "audit_type_id": "internal",
                    "audit_objects": [{"kind": "process", "object_id": "PROC-7"}],
                    "team": [{"auditor_id": "auditor-1", "role": "lead_auditor"}],
                    "planned_date": "2026-11-01T09:00:00+03:00",
                }
            ]
        },
    )

    title: str = Field(min_length=1, max_length=300)
    objective: str = ""
    scope: str = ""
    audit_type_id: str | None = Field(default=None, min_length=1)
    audit_programme_id: str | None = Field(default=None, min_length=1)
    audit_objects: list[AuditObjectRefDTO] = Field(default_factory=list)
    team: list[AuditTeamMemberDTO] = Field(default_factory=list)
    criteria: list[AuditCriterionDTO] = Field(default_factory=list)
    planned_date: AwareDatetime | None = None
    security_classification_id: str | None = Field(default=None, min_length=1)


class AuditResponse(BaseModel):
    """Response body describing the full state of an audit."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    created_at: datetime
    status: AuditStatus
    title: str
    objective: str
    scope: str
    audit_type_id: str | None
    audit_programme_id: str | None
    audit_objects: list[AuditObjectRefDTO]
    team: list[AuditTeamMemberDTO]
    lead_auditor: str | None
    criteria: list[AuditCriterionDTO]
    planned_date: datetime | None
    security_classification_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    closed_at: datetime | None
    report: AuditReportRefDTO | None
    report_approval: AuditReportApprovalDTO | None
    deferred_at: datetime | None
    deferred_from_status: AuditStatus | None
    last_defer_reason: str | None
    cancelled_at: datetime | None
    last_cancel_reason: str | None
    reopened_at: datetime | None
    last_reopen_reason: str | None

    @classmethod
    def from_domain(cls, audit: Audit) -> Self:
        """Map an ``Audit`` aggregate to its API representation."""
        return cls(
            id=UUID(audit.id),
            created_at=audit.created_at,
            status=audit.status,
            title=audit.title,
            objective=audit.objective,
            scope=audit.scope,
            audit_type_id=(
                None if audit.audit_type is None else audit.audit_type.audit_type_id
            ),
            audit_programme_id=audit.audit_programme_id,
            audit_objects=[
                AuditObjectRefDTO.from_domain(item) for item in audit.audit_objects
            ],
            team=[AuditTeamMemberDTO.from_domain(item) for item in audit.team],
            lead_auditor=audit.lead_auditor,
            criteria=[AuditCriterionDTO.from_domain(item) for item in audit.criteria],
            planned_date=audit.planned_date,
            security_classification_id=audit.security_classification_id,
            started_at=audit.started_at,
            completed_at=audit.completed_at,
            closed_at=audit.closed_at,
            report=(
                None
                if audit.report is None
                else AuditReportRefDTO.from_domain(audit.report)
            ),
            report_approval=(
                None
                if audit.report_approval is None
                else AuditReportApprovalDTO.from_domain(audit.report_approval)
            ),
            deferred_at=audit.deferred_at,
            deferred_from_status=audit.deferred_from_status,
            last_defer_reason=audit.last_defer_reason,
            cancelled_at=audit.cancelled_at,
            last_cancel_reason=audit.last_cancel_reason,
            reopened_at=audit.reopened_at,
            last_reopen_reason=audit.last_reopen_reason,
        )


class ErrorResponse(BaseModel):
    """Error body returned for mapped service and storage errors."""

    detail: str


# ---------------------------------------------------------------------------
# Dependency injection (MVP composition root)
# ---------------------------------------------------------------------------


def get_data_dir() -> Path:
    """Return the JSON data directory from the environment or the default."""
    configured = os.environ.get(DATA_DIR_ENV_VAR, "").strip()
    return Path(configured) if configured else DEFAULT_DATA_DIR


@lru_cache(maxsize=1)
def get_audit_service() -> AuditService:
    """Return the application-wide ``AuditService``.

    The service and its JSON repository are created once, on first use, and
    reused by every request. The repository synchronizes file access with a
    file lock, so sharing it between worker threads is safe. If creation
    fails, nothing is cached and the next request retries.

    Tests replace this dependency through ``app.dependency_overrides``.
    """
    return AuditService(JsonAuditRepository(get_data_dir()))


AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]


# ---------------------------------------------------------------------------
# Application and error mapping
# ---------------------------------------------------------------------------

app = FastAPI(title="Audit System API", version="0.1.0")

_ERROR_RESPONSES: Final[dict[int | str, dict[str, object]]] = {
    http_status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponse,
        "description": "Storage failure",
    },
}
_NOT_FOUND_RESPONSE: Final[dict[int | str, dict[str, object]]] = {
    http_status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "Audit not found",
    },
}


@app.exception_handler(NotFoundError)
async def handle_not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
    """Map a missing entity to HTTP 404."""
    return JSONResponse(
        status_code=http_status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(DomainValidationError)
async def handle_domain_validation(
    _request: Request,
    exc: DomainValidationError,
) -> JSONResponse:
    """Map invalid use-case input to HTTP 422 (ARCHITECTURE.md §53)."""
    return JSONResponse(
        status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": str(exc)},
    )


@app.exception_handler(StorageError)
async def handle_storage_error(request: Request, exc: StorageError) -> JSONResponse:
    """Map any other storage failure to HTTP 500.

    The client receives a generic message; the full error, which may contain
    file paths, is written to the server log only.
    """
    logger.error(
        "Storage failure during %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": STORAGE_FAILURE_DETAIL},
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/audits",
    status_code=http_status.HTTP_201_CREATED,
    tags=["audits"],
    summary="Create a new audit",
    responses=_ERROR_RESPONSES,
)
def create_audit(
    request: CreateAuditRequest,
    response: Response,
    service: AuditServiceDep,
) -> AuditResponse:
    """Create a new DRAFT audit and return it with a ``Location`` header."""
    try:
        audit_type = (
            None
            if request.audit_type_id is None
            else AuditTypeRef(request.audit_type_id)
        )
        audit_objects = [item.to_domain() for item in request.audit_objects]
        team = [item.to_domain() for item in request.team]
        criteria = [item.to_domain() for item in request.criteria]
    except (TypeError, ValueError) as exc:
        raise DomainValidationError(f"Cannot create audit: {exc}") from exc

    audit = service.create_audit(
        request.title,
        objective=request.objective,
        scope=request.scope,
        audit_type=audit_type,
        audit_programme_id=request.audit_programme_id,
        audit_objects=audit_objects,
        team=team,
        criteria=criteria,
        planned_date=request.planned_date,
        security_classification_id=request.security_classification_id,
    )

    response.headers["Location"] = app.url_path_for("get_audit", audit_id=audit.id)
    return AuditResponse.from_domain(audit)


@app.get(
    "/audits",
    tags=["audits"],
    summary="List audits",
    responses=_ERROR_RESPONSES,
)
def list_audits(
    service: AuditServiceDep,
    status: Annotated[
        str | None,
        Query(
            description=(
                "Optional lifecycle status filter (case-insensitive). "
                f"Allowed values: {_ALLOWED_STATUSES}."
            ),
        ),
    ] = None,
) -> list[AuditResponse]:
    """Return all audits ordered by creation time, optionally by status."""
    return [
        AuditResponse.from_domain(audit) for audit in service.list_audits(status=status)
    ]


@app.get(
    "/audits/{audit_id}",
    tags=["audits"],
    summary="Get an audit by id",
    responses={**_NOT_FOUND_RESPONSE, **_ERROR_RESPONSES},
)
def get_audit(audit_id: UUID, service: AuditServiceDep) -> AuditResponse:
    """Return a single audit."""
    return AuditResponse.from_domain(service.get_audit(audit_id))


@app.delete(
    "/audits/{audit_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["audits"],
    summary="Delete an audit",
    responses={**_NOT_FOUND_RESPONSE, **_ERROR_RESPONSES},
)
def delete_audit(audit_id: UUID, service: AuditServiceDep) -> None:
    """Delete an audit permanently."""
    service.delete_audit(audit_id)
