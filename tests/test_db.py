import pytest
from moto import mock_aws
from sample_polls import (
    ALL_SAMPLE_POLLDATA,
    LIBRARY_HOURS_POLLDATA,
    LUNCH_SPOT_POLLDATA,
    STUDY_SPOT_POLLDATA,
)

from voting.db import (
    DatabaseUnavailableError,
    InvalidOptionError,
    PollAlreadyExistsError,
    PollNotFoundError,
    PollStorage,
)

# TABLE_NAME / REGION and aws_credentials / polls_table / store fixtures
# live in conftest.py (shared with test_app.py).


def test_init_requires_table_name():
    with pytest.raises(ValueError, match="table_name"):
        PollStorage(table_name="", region_name="us-east-1")


def test_init_requires_region_name():
    with pytest.raises(ValueError, match="region_name"):
        PollStorage(table_name="Polls", region_name="")


def test_ping_succeeds_when_table_exists(store):
    # ping() returns None on success. No exception means the test passes.
    store.ping()


def test_ping_raises_when_table_missing(aws_credentials):
    # Only uses aws_credentials from the fixture chain — not polls_table —
    # so moto is on but the Polls table was never created.
    with mock_aws():
        store = PollStorage(table_name="Polls", region_name="us-east-1")
        with pytest.raises(DatabaseUnavailableError):
            store.ping()


def test_add_and_get_poll(store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    loaded = store.get_poll(LUNCH_SPOT_POLLDATA.poll_id)
    assert loaded == LUNCH_SPOT_POLLDATA


def test_get_poll_returns_none_when_missing(store):
    assert store.get_poll("does-not-exist") is None


def test_add_poll_raises_when_id_exists(store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    with pytest.raises(PollAlreadyExistsError):
        store.add_poll(LUNCH_SPOT_POLLDATA)


def test_list_polls_empty(store):
    assert store.list_polls() == []


def test_clear_all_removes_every_poll(store):
    store.add_poll(LUNCH_SPOT_POLLDATA)
    store.add_poll(LIBRARY_HOURS_POLLDATA)
    store.clear_all()
    assert store.list_polls() == []


def test_list_polls_returns_all(store):
    # Two differently shaped samples: min options vs max options.
    store.add_poll(LIBRARY_HOURS_POLLDATA)
    store.add_poll(STUDY_SPOT_POLLDATA)

    polls = store.list_polls()
    # list_polls does not sort; compare membership, not order.
    assert len(polls) == 2
    assert LIBRARY_HOURS_POLLDATA in polls
    assert STUDY_SPOT_POLLDATA in polls


def test_list_polls_returns_every_sample(store):
    for poll in ALL_SAMPLE_POLLDATA:
        store.add_poll(poll)

    polls = store.list_polls()
    assert len(polls) == len(ALL_SAMPLE_POLLDATA)
    for poll in ALL_SAMPLE_POLLDATA:
        assert poll in polls


def test_increment_vote(store):
    store.add_poll(LUNCH_SPOT_POLLDATA)

    updated = store.increment_vote(LUNCH_SPOT_POLLDATA.poll_id, 2)

    assert updated.options[1]["votes"] == 22  # HUB was 21
    assert updated.options[0]["votes"] == 10
    assert updated.options[2]["votes"] == 8
    assert updated.options[3]["votes"] == 4
    assert store.get_poll(LUNCH_SPOT_POLLDATA.poll_id) == updated


def test_increment_vote_raises_when_poll_missing(store):
    with pytest.raises(PollNotFoundError):
        store.increment_vote("does-not-exist", 1)


def test_increment_vote_raises_when_option_invalid(store):
    # LIBRARY_HOURS only has options 1 and 2.
    store.add_poll(LIBRARY_HOURS_POLLDATA)
    with pytest.raises(InvalidOptionError):
        store.increment_vote(LIBRARY_HOURS_POLLDATA.poll_id, 3)
