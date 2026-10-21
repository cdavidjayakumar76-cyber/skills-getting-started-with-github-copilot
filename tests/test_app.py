import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    isolated_activities = copy.deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data_and_participants(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Art Club" in activities
    assert activities["Art Club"]["participants"] == []
    assert all(isinstance(activity["participants"], list) for activity in activities.values())


def test_signup_adds_participant(client):
    email = "student@example.edu"

    response = client.post("/activities/Art Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Art Club"}
    activities = client.get("/activities").json()
    assert email in activities["Art Club"]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup", params={"email": "student@example.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_without_adding_participant_again(client):
    email = "student@example.edu"
    url = "/activities/Art Club/signup"

    assert client.post(url, params={"email": email}).status_code == 200
    response = client.post(url, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    participants = client.get("/activities").json()["Art Club"]["participants"]
    assert participants.count(email) == 1


def test_unregister_removes_participant(client):
    email = "student@example.edu"
    url = "/activities/Art Club/signup"
    client.post(url, params={"email": email})

    response = client.delete(url, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Art Club"}
    participants = client.get("/activities").json()["Art Club"]["participants"]
    assert email not in participants


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup", params={"email": "student@example.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        "/activities/Art Club/signup", params={"email": "student@example.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"