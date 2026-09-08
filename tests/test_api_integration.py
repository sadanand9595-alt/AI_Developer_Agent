"""
Integration tests for the HTTP API layer: authentication,
authorization, IDOR prevention, and execution (task lifecycle)
endpoints.

Uses FastAPI's TestClient against the real app (real SQLAlchemy
session per request, same database the rest of the test suite
uses) -- no mocking of the service layer.
"""

from __future__ import annotations

import threading
import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.security import hash_password
from database.session import session_scope
from services.user_service import UserService


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4()}@example.com"


def _register_and_login(
    client: TestClient,
    *,
    prefix: str,
    password: str = "correct-horse-battery",
) -> tuple[str, str, str]:
    """Register + login a fresh user. Returns (token, user_id, email)."""

    email = _unique_email(prefix)

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "name": f"{prefix} User",
            "password": password,
        },
    )
    assert register_response.status_code == 201, (
        register_response.text
    )
    user_id = register_response.json()["id"]

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    return token, user_id, email


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_admin(password: str = "admin-password-1") -> tuple[str, str]:
    """
    Create an admin user directly through the service layer.

    Public registration deliberately cannot self-promote to admin,
    so tests that need an admin bypass the API for setup only, the
    same way other admin-privileged fixtures would in a real system
    (e.g. a seeded operator account).
    """

    email = _unique_email("admin")

    with session_scope() as session:
        user = UserService(session).create_user(
            email=email,
            name="Admin User",
            password_hash=hash_password(password),
            is_admin=True,
        )
        user_id = user.id

    return email, user_id


# ---------------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------------


def test_register_and_login_success(client: TestClient) -> None:
    token, user_id, email = _register_and_login(
        client, prefix="auth-success"
    )

    assert token
    assert user_id


def test_register_duplicate_email_rejected(
    client: TestClient,
) -> None:
    email = _unique_email("dup")
    payload = {
        "email": email,
        "name": "Dup User",
        "password": "password-123",
    }

    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_malformed_email_rejected(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "name": "X",
            "password": "password-123",
        },
    )

    assert response.status_code == 422


def test_register_short_password_rejected(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": _unique_email("short-pw"),
            "name": "X",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_login_wrong_password_rejected(
    client: TestClient,
) -> None:
    email = _unique_email("wrong-pw")

    client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "Wrong PW",
            "password": "the-real-password",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "not-the-password"},
    )

    assert response.status_code == 401


def test_login_nonexistent_user_rejected(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": "nobody-here@example.com",
            "password": "whatever",
        },
    )

    assert response.status_code == 401


def test_protected_endpoint_requires_token(
    client: TestClient,
) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/auth/me",
        headers=_auth_headers("not-a-real-token"),
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# TASK OWNERSHIP / IDOR
# ---------------------------------------------------------------------------


def test_task_lifecycle_happy_path(client: TestClient) -> None:
    token, _, _ = _register_and_login(client, prefix="task-owner")
    headers = _auth_headers(token)

    create_response = client.post(
        "/tasks",
        json={
            "title": "Do the thing",
            "description": "A task created through the API.",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    task = create_response.json()
    assert task["status"] == "pending"

    start_response = client.post(
        f"/tasks/{task['id']}/start",
        headers=headers,
    )
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "running"

    complete_response = client.post(
        f"/tasks/{task['id']}/complete",
        json={"result": {"ok": True}},
        headers=headers,
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"

    # Terminal-state guard (from the already-audited Task model)
    # surfaces cleanly as 400 through the API, not a raw 500.
    recomplete_response = client.post(
        f"/tasks/{task['id']}/complete",
        json={"result": {"ok": True}},
        headers=headers,
    )
    assert recomplete_response.status_code == 400


def test_task_state_transitions_reject_invalid_paths(
    client: TestClient,
) -> None:
    token, _, _ = _register_and_login(
        client, prefix="task-invalid-state"
    )
    headers = _auth_headers(token)

    running_task = client.post(
        "/tasks",
        json={
            "title": "Running task",
            "description": "This task should reject double start.",
        },
        headers=headers,
    )
    running_id = running_task.json()["id"]
    first_start = client.post(
        f"/tasks/{running_id}/start",
        headers=headers,
    )
    assert first_start.status_code == 200
    second_start = client.post(
        f"/tasks/{running_id}/start",
        headers=headers,
    )
    assert second_start.status_code == 400
    assert second_start.json()["error"]["code"] == "VALIDATION_ERROR"

    completed_task = client.post(
        "/tasks",
        json={
            "title": "Completed task",
            "description": "This task should reject invalid completion.",
        },
        headers=headers,
    )
    completed_id = completed_task.json()["id"]
    assert client.post(f"/tasks/{completed_id}/start", headers=headers).status_code == 200
    assert client.post(
        f"/tasks/{completed_id}/complete",
        json={"result": {"ok": True}},
        headers=headers,
    ).status_code == 200
    assert client.post(
        f"/tasks/{completed_id}/complete",
        json={"result": {"ok": True}},
        headers=headers,
    ).status_code == 400
    assert client.post(
        f"/tasks/{completed_id}/fail",
        json={"error": {"code": "COMPLETED_TASK", "message": "Should fail."}},
        headers=headers,
    ).status_code == 400

    failed_task = client.post(
        "/tasks",
        json={
            "title": "Failed task",
            "description": "This task should allow retry startup.",
        },
        headers=headers,
    )
    failed_id = failed_task.json()["id"]
    assert client.post(f"/tasks/{failed_id}/start", headers=headers).status_code == 200
    assert client.post(
        f"/tasks/{failed_id}/fail",
        json={"error": {"code": "EXAMPLE_FAILURE", "message": "Retry later."}},
        headers=headers,
    ).status_code == 200
    assert client.post(
        f"/tasks/{failed_id}/fail",
        json={"error": {"code": "SECOND_FAIL", "message": "Invalid double fail."}},
        headers=headers,
    ).status_code == 400
    assert client.post(
        f"/tasks/{failed_id}/complete",
        json={"result": {"ok": True}},
        headers=headers,
    ).status_code == 400

    retried_start = client.post(
        f"/tasks/{failed_id}/start",
        headers=headers,
    )
    assert retried_start.status_code == 200
    assert retried_start.json()["status"] == "running"


def test_task_ownership_blocks_cross_user_access(
    client: TestClient,
) -> None:
    owner_token, _, _ = _register_and_login(
        client, prefix="task-idor-owner"
    )
    attacker_token, _, _ = _register_and_login(
        client, prefix="task-idor-attacker"
    )

    create_response = client.post(
        "/tasks",
        json={
            "title": "Owner's private task",
            "description": "Should not be visible to others.",
        },
        headers=_auth_headers(owner_token),
    )
    task_id = create_response.json()["id"]

    # Attacker supplies a valid, real task_id belonging to someone
    # else. Every route must return 404, not 403 or the task data.
    attacker_headers = _auth_headers(attacker_token)

    get_response = client.get(
        f"/tasks/{task_id}",
        headers=attacker_headers,
    )
    assert get_response.status_code == 404

    start_response = client.post(
        f"/tasks/{task_id}/start",
        headers=attacker_headers,
    )
    assert start_response.status_code == 404

    complete_response = client.post(
        f"/tasks/{task_id}/complete",
        json={},
        headers=attacker_headers,
    )
    assert complete_response.status_code == 404

    # The owner can still access their own task normally.
    owner_get = client.get(
        f"/tasks/{task_id}",
        headers=_auth_headers(owner_token),
    )
    assert owner_get.status_code == 200


def test_task_list_only_returns_own_tasks(
    client: TestClient,
) -> None:
    token_a, _, _ = _register_and_login(client, prefix="list-a")
    token_b, _, _ = _register_and_login(client, prefix="list-b")

    client.post(
        "/tasks",
        json={"title": "A's task", "description": "d"},
        headers=_auth_headers(token_a),
    )
    client.post(
        "/tasks",
        json={"title": "B's task", "description": "d"},
        headers=_auth_headers(token_b),
    )

    a_tasks = client.get(
        "/tasks", headers=_auth_headers(token_a)
    ).json()
    b_tasks = client.get(
        "/tasks", headers=_auth_headers(token_b)
    ).json()

    assert all(t["title"] == "A's task" for t in a_tasks)
    assert all(t["title"] == "B's task" for t in b_tasks)


# ---------------------------------------------------------------------------
# CONVERSATION / MESSAGE OWNERSHIP + IDOR
# ---------------------------------------------------------------------------


def test_conversation_and_message_ownership(
    client: TestClient,
) -> None:
    owner_token, _, _ = _register_and_login(
        client, prefix="conv-owner"
    )
    attacker_token, _, _ = _register_and_login(
        client, prefix="conv-attacker"
    )

    convo_response = client.post(
        "/conversations",
        json={"title": "Private conversation"},
        headers=_auth_headers(owner_token),
    )
    conversation_id = convo_response.json()["id"]

    # Owner can post a message normally.
    owner_message = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "Hello from the owner."},
        headers=_auth_headers(owner_token),
    )
    assert owner_message.status_code == 201

    attacker_headers = _auth_headers(attacker_token)

    get_response = client.get(
        f"/conversations/{conversation_id}",
        headers=attacker_headers,
    )
    assert get_response.status_code == 404

    message_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "Injected by an attacker."},
        headers=attacker_headers,
    )
    assert message_response.status_code == 404

    list_messages_response = client.get(
        f"/conversations/{conversation_id}/messages",
        headers=attacker_headers,
    )
    assert list_messages_response.status_code == 404


def test_message_rejected_for_archived_conversation(
    client: TestClient,
) -> None:
    token, _, _ = _register_and_login(
        client, prefix="conv-archive"
    )
    headers = _auth_headers(token)

    convo_response = client.post(
        "/conversations",
        json={"title": "To be archived"},
        headers=headers,
    )
    conversation_id = convo_response.json()["id"]

    archive_response = client.post(
        f"/conversations/{conversation_id}/archive",
        headers=headers,
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["is_archived"] is True

    message_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "Should be rejected."},
        headers=headers,
    )
    assert message_response.status_code == 400


def test_message_rejected_for_nonexistent_conversation(
    client: TestClient,
) -> None:
    token, _, _ = _register_and_login(
        client, prefix="conv-missing"
    )

    response = client.post(
        "/conversations/nonexistent-conversation-id/messages",
        json={"content": "x"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# APPROVAL AUTHORIZATION
# ---------------------------------------------------------------------------


def test_non_admin_cannot_approve(client: TestClient) -> None:
    token, user_id, _ = _register_and_login(
        client, prefix="approval-requester"
    )

    with session_scope() as session:
        from services.approval_service import ApprovalService

        approval = ApprovalService(session).request_approval(
            user_id=user_id,
            action="delete_file",
            reason="Testing approval authorization.",
            requested_operation="Delete a file.",
        )
        approval_id = approval.id

    response = client.post(
        f"/approvals/{approval_id}/approve",
        json={},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403


def test_admin_can_approve(client: TestClient) -> None:
    requester_token, requester_id, _ = _register_and_login(
        client, prefix="approval-requester-2"
    )
    admin_email, admin_id = _create_admin()

    admin_login = client.post(
        "/auth/login",
        json={
            "email": admin_email,
            "password": "admin-password-1",
        },
    )
    admin_token = admin_login.json()["access_token"]

    with session_scope() as session:
        from services.approval_service import ApprovalService

        approval = ApprovalService(session).request_approval(
            user_id=requester_id,
            action="delete_file",
            reason="Testing admin approval.",
            requested_operation="Delete a file.",
        )
        approval_id = approval.id

    approve_response = client.post(
        f"/approvals/{approval_id}/approve",
        json={"comment": "Looks fine."},
        headers=_auth_headers(admin_token),
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"


def test_approval_hidden_from_unrelated_user(
    client: TestClient,
) -> None:
    requester_token, requester_id, _ = _register_and_login(
        client, prefix="approval-owner-3"
    )
    outsider_token, _, _ = _register_and_login(
        client, prefix="approval-outsider"
    )

    with session_scope() as session:
        from services.approval_service import ApprovalService

        approval = ApprovalService(session).request_approval(
            user_id=requester_id,
            action="delete_file",
            reason="Testing approval visibility.",
            requested_operation="Delete a file.",
        )
        approval_id = approval.id

    outsider_response = client.get(
        f"/approvals/{approval_id}",
        headers=_auth_headers(outsider_token),
    )
    assert outsider_response.status_code == 404

    owner_response = client.get(
        f"/approvals/{approval_id}",
        headers=_auth_headers(requester_token),
    )
    assert owner_response.status_code == 200


# ---------------------------------------------------------------------------
# SECURITY AUDIT REGRESSION TESTS
# ---------------------------------------------------------------------------


def test_login_timing_does_not_reveal_account_existence(
    client: TestClient,
) -> None:
    """
    A login attempt for a nonexistent email must take roughly the
    same time as one for a real email with a wrong password.

    Before the fix, a nonexistent email short-circuited before
    hashing, making it ~50x faster than a real email + wrong
    password (measured live) -- an account-enumeration side channel
    even though the error message itself was already identical.
    A generous 5x threshold tolerates CI/test-runner jitter while
    still catching a regression back to the short-circuit, which
    was ~50x.
    """

    email = _unique_email("timing")
    client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "Timing Test",
            "password": "correct-horse-battery",
        },
    )

    def median_login_time(
        login_email: str,
        attempts: int = 9,
    ) -> float:
        samples = []

        for _ in range(attempts):
            start = time.perf_counter()
            client.post(
                "/auth/login",
                json={
                    "email": login_email,
                    "password": "wrong-password",
                },
            )
            samples.append(time.perf_counter() - start)

        samples.sort()
        return samples[len(samples) // 2]

    existing_user_time = median_login_time(email)
    nonexistent_user_time = median_login_time(
        _unique_email("nobody")
    )

    ratio = existing_user_time / max(
        nonexistent_user_time, 1e-6
    )

    assert ratio < 5, (
        "Login timing leaks account existence: existing-user "
        f"median={existing_user_time:.4f}s vs nonexistent-user "
        f"median={nonexistent_user_time:.4f}s (ratio={ratio:.1f}x)"
    )


def test_concurrent_duplicate_registration_never_returns_500() -> None:
    """
    A concurrent duplicate-email registration race must always
    surface as a controlled 400, never a raw, uncontrolled 500 from
    an escaped IntegrityError (which also risks leaking internal
    schema details in server logs/tracebacks).
    """

    raw_client = TestClient(app, raise_server_exceptions=False)
    email = _unique_email("concurrent-register")

    results: list[int] = []
    lock = threading.Lock()

    def worker() -> None:
        response = raw_client.post(
            "/auth/register",
            json={
                "email": email,
                "name": "Concurrent",
                "password": "password-123456",
            },
        )
        with lock:
            results.append(response.status_code)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count(201) == 1
    assert results.count(500) == 0
    assert all(code in (201, 400) for code in results)


def test_concurrent_approval_never_double_approves() -> None:
    """
    Two concurrent approve() calls for the same request must not
    both succeed. Before the fix, both callers could receive 200
    while the second silently overwrote the first reviewer's
    decision (a lost update / double-approval race).
    """

    raw_client = TestClient(app, raise_server_exceptions=False)

    requester_email = _unique_email("concurrent-approval-req")
    requester_register = raw_client.post(
        "/auth/register",
        json={
            "email": requester_email,
            "name": "Requester",
            "password": "password-123456",
        },
    )
    requester_id = requester_register.json()["id"]

    admin_email = _unique_email("concurrent-approval-admin")
    admin_password = "admin-password-123456"

    with session_scope() as session:
        admin = UserService(session).create_user(
            email=admin_email,
            name="Admin",
            password_hash=hash_password(admin_password),
            is_admin=True,
        )
        admin_id = admin.id

    admin_login = raw_client.post(
        "/auth/login",
        json={"email": admin_email, "password": admin_password},
    )
    admin_headers = _auth_headers(
        admin_login.json()["access_token"]
    )

    with session_scope() as session:
        from services.approval_service import ApprovalService

        approval = ApprovalService(session).request_approval(
            user_id=requester_id,
            action="delete_file",
            reason="Testing concurrent approval.",
            requested_operation="Delete a file.",
        )
        approval_id = approval.id

    results: list[int] = []
    lock = threading.Lock()

    def worker() -> None:
        response = raw_client.post(
            f"/approvals/{approval_id}/approve",
            json={},
            headers=admin_headers,
        )
        with lock:
            results.append(response.status_code)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count(200) == 1
    assert results.count(500) == 0
    assert all(code in (200, 400) for code in results)

    with session_scope() as session:
        from database.repositories.approval_repository import (
            ApprovalRepository,
        )

        final = ApprovalRepository(session).get_by_id(
            approval_id
        )
        assert final.status == "approved"
        assert final.reviewed_by == admin_id


def test_task_creation_rejects_other_users_conversation_id(
    client: TestClient,
) -> None:
    owner_token, _, _ = _register_and_login(
        client, prefix="task-conv-owner"
    )
    attacker_token, _, _ = _register_and_login(
        client, prefix="task-conv-attacker"
    )

    convo = client.post(
        "/conversations",
        json={"title": "Owner convo"},
        headers=_auth_headers(owner_token),
    ).json()

    response = client.post(
        "/tasks",
        json={
            "title": "x",
            "description": "d",
            "conversation_id": convo["id"],
        },
        headers=_auth_headers(attacker_token),
    )

    assert response.status_code == 404
