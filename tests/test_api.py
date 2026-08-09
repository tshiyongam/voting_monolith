import pytest
from moto import mock_aws
from sample_polls import (
    LUNCH_SPOT_POLLDATA,
    LUNCH_SPOT_POLLQUESTION,
    LUNCH_SPOT_POLLRESULTS,
    MEETUP_NO_VOTES_POLLDATA,
)

from voting.app import create_app
from voting.db import PollStorage
from voting.voting import VotingApp


@pytest.fixture
def client(store):
    voting_app = VotingApp(store)
    flask_app = create_app(voting_app)
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_unavailable(aws_credentials):
    # moto is on, but we never create the Polls table — ping/health should fail.
    with mock_aws():
        store = PollStorage(table_name="Polls", region_name="us-east-1")
        client = create_app(VotingApp(store)).test_client()
        response = client.get("/health")
        assert response.status_code == 503
        assert response.get_json() == {"status": "unavailable"}


def test_list_polls_empty(client):
    response = client.get("/polls")
    assert response.status_code == 200
    assert response.get_json() == {"polls": []}


def test_list_polls(client, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    store.add_poll(MEETUP_NO_VOTES_POLLDATA)

    response = client.get("/polls")
    assert response.status_code == 200
    assert response.get_json() == {
        "polls": [
            {
                "id": MEETUP_NO_VOTES_POLLDATA.poll_id,
                "question": MEETUP_NO_VOTES_POLLDATA.question,
                "totalVotes": 0,
            },
            {
                "id": LUNCH_SPOT_POLLDATA.poll_id,
                "question": LUNCH_SPOT_POLLDATA.question,
                "totalVotes": 43,
            },
        ]
    }


def test_create_poll(client):
    response = client.post(
        "/polls",
        json={"question": "Favorite color?", "options": ["Red", "Blue"]},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert "id" in body
    assert len(body["id"]) == 8


def test_create_poll_bad_request(client):
    response = client.post(
        "/polls",
        json={"question": "Only one?", "options": ["Alone"]},
    )
    assert response.status_code == 400
    body = response.get_json()
    assert body["error"]["code"] == "BAD_REQUEST"
    assert "message" in body["error"]


def test_get_poll(client, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    response = client.get(f"/polls/{LUNCH_SPOT_POLLDATA.poll_id}")
    assert response.status_code == 200
    assert response.get_json() == {
        "id": LUNCH_SPOT_POLLQUESTION.id,
        "question": LUNCH_SPOT_POLLQUESTION.question,
        "options": LUNCH_SPOT_POLLQUESTION.options,
        "totalVotes": LUNCH_SPOT_POLLQUESTION.total_votes,
    }


def test_get_poll_not_found(client):
    response = client.get("/polls/does-not-exist")
    assert response.status_code == 404
    assert response.get_json() == {
        "error": {"code": "POLL_NOT_FOUND", "message": "Poll not found"}
    }


def test_get_results(client, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    response = client.get(f"/polls/{LUNCH_SPOT_POLLDATA.poll_id}/results")
    assert response.status_code == 200
    assert response.get_json() == {
        "id": LUNCH_SPOT_POLLRESULTS.id,
        "question": LUNCH_SPOT_POLLRESULTS.question,
        "totalVotes": LUNCH_SPOT_POLLRESULTS.total_votes,
        "results": LUNCH_SPOT_POLLRESULTS.results,
    }


def test_cast_vote(client, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    response = client.post(f"/polls/{LUNCH_SPOT_POLLDATA.poll_id}/votes?option=2")
    assert response.status_code == 200
    body = response.get_json()
    assert body["results"][1]["votes"] == 22
    assert body["totalVotes"] == 44


def test_cast_vote_missing_option(client, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    response = client.post(f"/polls/{LUNCH_SPOT_POLLDATA.poll_id}/votes")
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "BAD_REQUEST"


def test_cast_vote_not_found(client):
    response = client.post("/polls/does-not-exist/votes?option=1")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "POLL_NOT_FOUND"


@pytest.mark.parametrize(
    "path",
    ["/", "/create", "/vote", "/results", "/static/styles.css"],
)
def test_ui_pages_are_served(client, path):
    response = client.get(path)
    assert response.status_code == 200
