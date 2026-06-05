import uuid

import pytest

pytestmark = pytest.mark.anyio


async def test_health_check_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_create_project_with_valid_data(client, auth_headers):
    response = await client.post(
        "/projects",
        json={
            "name": "my-valid-app",
            "git_url": "https://github.com/test/repo",
            "port": 3000,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "my-valid-app"
    assert data["status"] == "pending"


async def test_create_project_with_invalid_name(client, auth_headers):
    response = await client.post(
        "/projects",
        json={
            "name": "Invalid Name!",
            "git_url": "https://github.com/test/repo",
            "port": 3000,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_create_project_with_duplicate_name(
    client, auth_headers, existing_project
):
    response = await client.post(
        "/projects",
        json={
            "name": existing_project["name"],
            "git_url": "https://github.com/test/repo",
            "port": 3000,
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


async def test_list_projects_returns_own_projects(client, auth_headers):
    # create 2 projects
    for name in ["proj-one", "proj-two"]:
        await client.post(
            "/projects",
            json={
                "name": name,
                "git_url": "https://github.com/test/repo",
                "port": 3000,
            },
            headers=auth_headers,
        )
    response = await client.get("/projects", headers=auth_headers)
    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert "proj-one" in names
    assert "proj-two" in names


async def test_get_project_by_id(client, auth_headers, existing_project):
    response = await client.get(
        f"/projects/{existing_project['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == existing_project["name"]


async def test_get_project_not_found(client, auth_headers):
    response = await client.get(
        f"/projects/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_delete_project(client, auth_headers, existing_project):
    response = await client.delete(
        f"/projects/{existing_project['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # confirm it's gone
    response = await client.get(
        f"/projects/{existing_project['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_delete_project_wrong_owner(client, auth_headers, existing_project):
    from datetime import timedelta

    from common.utils import create_access_token

    other_token = create_access_token({"sub": str(uuid.uuid4())}, timedelta(minutes=30))
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = await client.delete(
        f"/projects/{existing_project['id']}",
        headers=other_headers,
    )
    assert response.status_code == 404
