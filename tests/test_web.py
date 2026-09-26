"""API tests for ``audit_sys.web.main`` using FastAPI's ``TestClient``.

The ``get_audit_service`` dependency is overridden so that every test runs
against a ``JsonAuditRepository`` located in an isolated ``tmp_path``
directory; the project's real ``data/`` directory is never touched.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from audit_sys.models.core import AuditClosureGate, AuditReportRef, AuditStatus
from audit_sys.services.audit_service import AuditService
from audit_sys.storage.json_storage import JsonAuditRepository
from audit_sys.web.main import (
    DATA_DIR_ENV_VAR,
    STORAGE_FAILURE_DETAIL,
    app,
    get_audit_service,
)

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def storage(tmp_path: Path) -> JsonAuditRepository:
    """Return a JSON repository in an isolated temporary directory."""
    return JsonAuditRepository(tmp_path / "data")


@pytest.fixture
def service(storage: JsonAuditRepository) -> AuditService:
    """Return an ``AuditService`` backed by the temporary repository."""
    return AuditService(storage)


@pytest.fixture
def client(service: AuditService) -> Iterator[TestClient]:
    """Return a ``TestClient`` whose service dependency uses ``tmp_path``."""
    app.dependency_overrides[get_audit_service] = lambda: service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_audit_service, None)


def _full_payload(title: str = "ISO 9001 internal audit") -> dict[str, Any]:
    """Return a complete, valid ``POST /audits`` request body."""
    return {
        "title": title,
        "objective": "Verify supplier control",
        "scope": "Production line A",
        "audit_type_id": "internal",
        "audit_programme_id": "PRG-2026",
        "audit_objects": [{"kind": "supplier", "object_id": "SUP-1"}],
        "team": [
            {"auditor_id": "auditor-1", "role": "lead_auditor"},
            {"auditor_id": "auditor-2"},
        ],
        "criteria": [
            {
                "criterion_id": "ISO9001-8.4",
                "version": "2015",
                "title": "Control of externally provided processes",
                "requirement_text": "The organization shall ensure ...",
                "source_type": "standard",
                "source_id": "ISO 9001",
                "clause": "8.4",
            }
        ],
        "planned_date": "2026-11-01T09:00:00+03:00",
        "security_classification_id": "internal",
    }


def _create(client: TestClient, payload: dict[str, Any]) -> dict[str, Any]:
    """Create an audit through the API and return the response body."""
    response = client.post("/audits", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def _move_to_status(
    service: AuditService,
    storage: JsonAuditRepository,
    audit_id: str,
    status: AuditStatus,
) -> None:
    """Advance a stored audit to ``status`` using the domain lifecycle."""
    audit = service.get_audit(UUID(audit_id))
    audit.plan()
    if status is AuditStatus.ISSUED:
        audit.issue()
    elif status is AuditStatus.CANCELLED:
        audit.cancel("No longer required")
    storage.save(audit)


@pytest.fixture
def mixed_audits(
    client: TestClient,
    service: AuditService,
    storage: JsonAuditRepository,
) -> dict[str, list[str]]:
    """Create audits in several statuses; return their ids grouped by status."""
    ids: dict[str, list[str]] = {}
    plan = [
        ("Draft A", AuditStatus.DRAFT),
        ("Draft B", AuditStatus.DRAFT),
        ("Planned A", AuditStatus.PLANNED),
        ("Issued A", AuditStatus.ISSUED),
        ("Cancelled A", AuditStatus.CANCELLED),
    ]
    for title, status in plan:
        audit_id = _create(client, _full_payload(title))["id"]
        if status is not AuditStatus.DRAFT:
            _move_to_status(service, storage, audit_id, status)
        ids.setdefault(status.value, []).append(audit_id)
    return ids


# ---------------------------------------------------------------------------
# POST /audits
# ---------------------------------------------------------------------------


def test_create_audit_with_minimal_body_returns_201(client: TestClient) -> None:
    response = client.post("/audits", json={"title": "Minimal audit"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Minimal audit"
    assert body["status"] == "draft"
    assert UUID(body["id"]).version == 4
    assert body["audit_objects"] == []
    assert body["team"] == []
    assert body["lead_auditor"] is None
    assert response.headers["location"] == f"/audits/{body['id']}"


def test_create_audit_returns_utc_created_at(client: TestClient) -> None:
    before = datetime.now(UTC)

    body = _create(client, {"title": "Timestamped audit"})

    created_at = datetime.fromisoformat(body["created_at"])
    assert created_at.utcoffset() == timedelta(0)
    assert before <= created_at <= datetime.now(UTC)


def test_create_audit_with_full_body_maps_all_fields(client: TestClient) -> None:
    body = _create(client, _full_payload("מבדק ספקים"))

    assert body["title"] == "מבדק ספקים"
    assert body["audit_type_id"] == "internal"
    assert body["audit_programme_id"] == "PRG-2026"
    assert body["audit_objects"] == [{"kind": "supplier", "object_id": "SUP-1"}]
    assert body["team"] == [
        {"auditor_id": "auditor-1", "role": "lead_auditor"},
        {"auditor_id": "auditor-2", "role": "auditor"},
    ]
    assert body["lead_auditor"] == "auditor-1"
    assert body["criteria"][0]["clause"] == "8.4"
    assert datetime.fromisoformat(body["planned_date"]) == datetime(
        2026, 11, 1, 6, 0, tzinfo=UTC
    )


def test_create_audit_persists_through_the_service(
    client: TestClient,
    service: AuditService,
) -> None:
    body = _create(client, _full_payload())

    stored = service.get_audit(UUID(body["id"]))
    assert stored.title == body["title"]
    assert stored.lead_auditor == "auditor-1"


def test_create_audit_response_does_not_expose_internal_fields(
    client: TestClient,
) -> None:
    body = _create(client, {"title": "Audit"})

    assert "_initialized" not in body
    assert not any(key.startswith("_") for key in body)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "x" * 301},
        {"title": 123},
        {"title": "Audit", "unexpected_field": "value"},
        {"title": "Audit", "planned_date": "2026-11-01T09:00:00"},
        {"title": "Audit", "planned_date": "not-a-date"},
        {"title": "Audit", "audit_objects": [{"kind": "planet", "object_id": "X"}]},
        {"title": "Audit", "team": [{"auditor_id": "a-1", "role": "boss"}]},
        {"title": "Audit", "audit_type_id": ""},
    ],
    ids=[
        "missing-title",
        "empty-title",
        "title-too-long",
        "non-string-title",
        "unknown-field",
        "naive-planned-date",
        "invalid-planned-date",
        "unknown-object-kind",
        "unknown-team-role",
        "empty-audit-type",
    ],
)
def test_create_audit_rejects_malformed_body_with_422(
    client: TestClient,
    payload: dict[str, Any],
) -> None:
    response = client.post("/audits", json=payload)

    assert response.status_code == 422
    assert client.get("/audits").json() == []


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"title": "   "}, "title cannot be empty"),
        ({"audit_type_id": "   "}, "audit_type_id cannot be empty"),
        (
            {"audit_objects": [{"kind": "site", "object_id": "   "}]},
            "object_id cannot be empty",
        ),
        (
            {
                "team": [
                    {"auditor_id": "a-1", "role": "lead_auditor"},
                    {"auditor_id": "a-2", "role": "lead_auditor"},
                ]
            },
            "only one Lead Auditor",
        ),
        (
            {
                "audit_objects": [
                    {"kind": "site", "object_id": "SITE-1"},
                    {"kind": "site", "object_id": "SITE-1"},
                ]
            },
            "duplicate references",
        ),
    ],
    ids=[
        "blank-title",
        "blank-audit-type",
        "blank-object-id",
        "two-lead-auditors",
        "duplicate-audit-objects",
    ],
)
def test_create_audit_maps_domain_violations_to_422(
    client: TestClient,
    overrides: dict[str, Any],
    message: str,
) -> None:
    payload = {"title": "Valid title", **overrides}

    response = client.post("/audits", json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, str)
    assert detail.startswith("Cannot create audit")
    assert message in detail
    assert client.get("/audits").json() == []


# ---------------------------------------------------------------------------
# GET /audits/{audit_id}
# ---------------------------------------------------------------------------


def test_get_existing_audit_returns_200_and_same_representation(
    client: TestClient,
) -> None:
    created = _create(client, _full_payload())

    response = client.get(f"/audits/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_closed_audit_includes_report_and_approval(
    client: TestClient,
    service: AuditService,
    storage: JsonAuditRepository,
) -> None:
    created = _create(client, _full_payload())
    audit = service.get_audit(UUID(created["id"]))
    start = audit.created_at
    audit.plan()
    audit.issue()
    audit.start(start + timedelta(hours=1))
    audit.attach_report(AuditReportRef("RPT-1", "1.0"))
    audit.complete(start + timedelta(hours=2))
    audit.approve_report("qa-manager", start + timedelta(hours=3))
    audit.close(AuditClosureGate(), start + timedelta(hours=4))
    storage.save(audit)

    body = client.get(f"/audits/{created['id']}").json()

    assert body["status"] == "closed"
    assert body["report"] == {"report_id": "RPT-1", "version": "1.0"}
    assert body["report_approval"]["report"] == body["report"]
    assert body["report_approval"]["approved_by"] == "qa-manager"
    assert datetime.fromisoformat(body["closed_at"]) == start + timedelta(hours=4)


def test_get_unknown_audit_returns_404(client: TestClient) -> None:
    missing_id = uuid4()

    response = client.get(f"/audits/{missing_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": f"Audit with id '{missing_id}' was not found."}


def test_get_audit_with_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.get("/audits/not-a-uuid")

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /audits
# ---------------------------------------------------------------------------


def test_list_audits_returns_empty_list_initially(client: TestClient) -> None:
    response = client.get("/audits")

    assert response.status_code == 200
    assert response.json() == []


def test_list_audits_returns_all_audits_in_service_order(
    client: TestClient,
) -> None:
    created = [_create(client, {"title": f"Audit {i}"}) for i in range(4)]
    expected_ids = [
        item["id"]
        for item in sorted(
            created,
            key=lambda item: (datetime.fromisoformat(item["created_at"]), item["id"]),
        )
    ]

    response = client.get("/audits")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == expected_ids


@pytest.mark.parametrize("status", ["draft", "planned", "issued", "cancelled"])
def test_list_audits_filters_by_status(
    client: TestClient,
    mixed_audits: dict[str, list[str]],
    status: str,
) -> None:
    response = client.get("/audits", params={"status": status})

    assert response.status_code == 200
    body = response.json()
    assert set(item["id"] for item in body) == set(mixed_audits[status])
    assert all(item["status"] == status for item in body)


@pytest.mark.parametrize("status_filter", ["PLANNED", " Planned "])
def test_list_audits_status_filter_is_case_insensitive(
    client: TestClient,
    mixed_audits: dict[str, list[str]],
    status_filter: str,
) -> None:
    response = client.get("/audits", params={"status": status_filter})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == mixed_audits["planned"]


def test_list_audits_with_status_without_matches_returns_empty_list(
    client: TestClient,
    mixed_audits: dict[str, list[str]],
) -> None:
    assert "closed" not in mixed_audits

    response = client.get("/audits", params={"status": "closed"})

    assert response.status_code == 200
    assert response.json() == []


def test_list_audits_with_unknown_status_returns_422(client: TestClient) -> None:
    response = client.get("/audits", params={"status": "archived"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Unknown audit status 'archived'" in detail
    assert "in_progress" in detail


# ---------------------------------------------------------------------------
# DELETE /audits/{audit_id}
# ---------------------------------------------------------------------------


def test_delete_existing_audit_returns_204_and_removes_it(
    client: TestClient,
) -> None:
    kept = _create(client, {"title": "Kept audit"})
    removed = _create(client, {"title": "Removed audit"})

    response = client.delete(f"/audits/{removed['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/audits/{removed['id']}").status_code == 404
    assert [item["id"] for item in client.get("/audits").json()] == [kept["id"]]


def test_delete_unknown_audit_returns_404(client: TestClient) -> None:
    missing_id = uuid4()

    response = client.delete(f"/audits/{missing_id}")

    assert response.status_code == 404
    assert str(missing_id) in response.json()["detail"]


def test_delete_same_audit_twice_returns_404(client: TestClient) -> None:
    audit = _create(client, {"title": "Audit"})

    assert client.delete(f"/audits/{audit['id']}").status_code == 204
    assert client.delete(f"/audits/{audit['id']}").status_code == 404


def test_delete_with_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.delete("/audits/not-a-uuid")

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Storage failures and wiring
# ---------------------------------------------------------------------------


def test_storage_failure_returns_500_without_leaking_details(
    client: TestClient,
    storage: JsonAuditRepository,
) -> None:
    storage.file_path.write_text("{corrupted", encoding="utf-8")

    response = client.get("/audits")

    assert response.status_code == 500
    assert response.json() == {"detail": STORAGE_FAILURE_DETAIL}
    assert str(storage.file_path) not in response.text


def test_default_dependency_uses_configured_data_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "configured-data"
    monkeypatch.setenv(DATA_DIR_ENV_VAR, str(data_dir))
    get_audit_service.cache_clear()
    try:
        with TestClient(app) as test_client:
            created = _create(test_client, {"title": "Default wiring"})

        assert (data_dir / "audits.json").is_file()
        assert get_audit_service() is get_audit_service()
        assert get_audit_service().get_audit(UUID(created["id"])).title == (
            "Default wiring"
        )
    finally:
        get_audit_service.cache_clear()


def test_openapi_schema_documents_all_endpoints(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"] == {"title": "Audit System API", "version": "0.1.0"}
    assert set(schema["paths"]["/audits"]) == {"get", "post"}
    assert set(schema["paths"]["/audits/{audit_id}"]) == {"get", "delete"}
