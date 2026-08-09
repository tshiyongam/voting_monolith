import pytest
from moto import mock_aws
from sample_polls import (
    LIBRARY_HOURS_POLLDATA,
    LUNCH_SPOT_POLLDATA,
    LUNCH_SPOT_POLLQUESTION,
    LUNCH_SPOT_POLLRESULTS,
    MEETUP_NO_VOTES_POLLDATA,
)

from voting.db import PollStorage
from voting.poll_types import extract_poll_summary
from voting.voting import (
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
    VotingApp,
)

# TABLE_NAME / REGION and aws_credentials / polls_table / store fixtures
# live in conftest.py (shared with test_db.py).


@pytest.fixture
def app(store):
    return VotingApp(store)


def test_health_ok(app):
    # health() returns None on success. No exception means the test passes.
    app.health()


def test_health_raises_when_table_missing(aws_credentials):
    with mock_aws():
        store = PollStorage(table_name="Polls", region_name="us-east-1")
        app = VotingApp(store)
        with pytest.raises(ServiceUnavailableError):
            app.health()


def test_create_poll_returns_id_and_stores(app, store):
    poll_id = app.create_poll(
        "  Favorite color?  ",
        ["  Red  ", "Blue", "Green"],
    )
    assert isinstance(poll_id, str)
    assert len(poll_id) == 8

    stored = store.get_poll(poll_id)
    assert stored is not None
    assert stored.question == "Favorite color?"
    assert stored.options == [
        {"number": 1, "text": "Red", "votes": 0},
        {"number": 2, "text": "Blue", "votes": 0},
        {"number": 3, "text": "Green", "votes": 0},
    ]


@pytest.mark.parametrize(
    "question, options",
    [
        ("", ["A", "B"]),  # empty question
        ("   ", ["A", "B"]),  # blank question (only whitespace)
        ("x" * 281, ["A", "B"]),  # question longer than 280 characters
        ("Q?", ["A"]),  # fewer than 2 options
        ("Q?", ["A", "B", "C", "D", "E", "F", "G"]),  # more than 6 options
        ("Q?", ["A", ""]),  # blank option label
        ("Q?", ["A", "x" * 101]),  # option longer than 100 characters
        ("Q?", ["Same", "Same"]),  # duplicate option labels
        ("Q?", ["  Trimmed  ", "Trimmed"]),  # duplicates after strip
    ],
)
def test_create_poll_validation(app, question, options):
    with pytest.raises(ValidationError):
        app.create_poll(question, options)


def test_list_polls_newest_first(app, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    store.add_poll(MEETUP_NO_VOTES_POLLDATA)

    summaries = app.list_polls()
    assert summaries == [
        extract_poll_summary(MEETUP_NO_VOTES_POLLDATA),
        extract_poll_summary(LUNCH_SPOT_POLLDATA),
    ]


def test_list_polls_empty(app):
    assert app.list_polls() == []


def test_get_poll(app, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    assert app.get_poll(LUNCH_SPOT_POLLDATA.poll_id) == LUNCH_SPOT_POLLQUESTION


def test_get_poll_not_found(app):
    with pytest.raises(NotFoundError):
        app.get_poll("does-not-exist")


def test_get_results(app, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    assert app.get_results(LUNCH_SPOT_POLLDATA.poll_id) == LUNCH_SPOT_POLLRESULTS


def test_get_results_not_found(app):
    with pytest.raises(NotFoundError):
        app.get_results("does-not-exist")


def test_cast_vote(app, store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    results = app.cast_vote(LUNCH_SPOT_POLLDATA.poll_id, 2)
    assert results.results[1]["votes"] == 22
    assert results.total_votes == 44


def test_cast_vote_not_found(app):
    with pytest.raises(NotFoundError):
        app.cast_vote("does-not-exist", 1)


def test_cast_vote_invalid_option(app, store):
    store.add_poll(LIBRARY_HOURS_POLLDATA)
    with pytest.raises(ValidationError):
        app.cast_vote(LIBRARY_HOURS_POLLDATA.poll_id, 3)


def test_list_includes_created_poll_summary(app):
    poll_id = app.create_poll("New one?", ["Yes", "No"])
    summaries = app.list_polls()
    assert len(summaries) == 1
    assert summaries[0].id == poll_id
    assert summaries[0].total_votes == 0
