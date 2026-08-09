"""Shared setup for Playwright acceptance tests.

Assumes DynamoDB Local and Flask are already running on the usual ports
(see docs/development.md). This file only checks that the app is healthy, exposes
base_url for pytest-playwright, and provides data fixtures via PollStorage.
"""

import urllib.error
import urllib.request

import pytest
from sample_polls import LUNCH_SPOT_POLLDATA, MEETUP_NO_VOTES_POLLDATA

from voting.db import PollStorage
from voting.settings import ensure_settings

# Same host/port as python -m voting.app (app.run(port=5000)).
BASE_URL = "http://127.0.0.1:5000"


def pytest_sessionstart(session):
    """Fail fast if the running app is not healthy."""
    health_url = f"{BASE_URL}/health"
    try:
        with urllib.request.urlopen(health_url, timeout=1.0) as response:
            if response.status != 200:
                pytest.exit(
                    f"{health_url} returned {response.status} (expected 200). "
                    "Is DynamoDB Local running? Is the Polls table created? "
                    "Is the app running (python -m voting.app)?",
                    returncode=1,
                )
    except (urllib.error.URLError, OSError) as exc:
        pytest.exit(
            f"App not reachable at {BASE_URL}. "
            "Start DynamoDB Local, create the Polls table, and run "
            "python -m voting.app (see docs/development.md).\n"
            f"Details: {exc}",
            returncode=1,
        )


@pytest.fixture(scope="session")
def base_url():
    """URL of the already-running Flask app (pytest-playwright uses this)."""
    return BASE_URL


@pytest.fixture
def poll_storage():
    """Empty PollStorage connected with ensure_settings (for arranging data)."""
    settings = ensure_settings()
    storage = PollStorage(
        table_name=settings["POLLS_TABLE_NAME"],
        region_name=settings["AWS_DEFAULT_REGION"],
        endpoint_url=settings["DYNAMODB_ENDPOINT_URL"],
    )
    storage.clear_all()
    return storage


@pytest.fixture
def lunch_spot_poll(poll_storage):
    """One sample poll with an existing vote spread (see data/sample-data.json)."""
    poll_storage.add_poll(LUNCH_SPOT_POLLDATA)
    return LUNCH_SPOT_POLLDATA


@pytest.fixture
def meetup_poll(poll_storage):
    """One sample poll with zero votes."""
    poll_storage.add_poll(MEETUP_NO_VOTES_POLLDATA)
    return MEETUP_NO_VOTES_POLLDATA


@pytest.fixture
def two_polls_newest_first(poll_storage):
    """Meetup (newer) and lunch spot (older) for browse-order checks."""
    poll_storage.add_poll(LUNCH_SPOT_POLLDATA)
    poll_storage.add_poll(MEETUP_NO_VOTES_POLLDATA)
    return (MEETUP_NO_VOTES_POLLDATA, LUNCH_SPOT_POLLDATA)
