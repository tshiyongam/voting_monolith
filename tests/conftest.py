import boto3
import pytest
from moto import mock_aws

from voting.db import PollStorage

TABLE_NAME = "Polls"
REGION = "us-east-1"

# conftest.py is a pytest convention: fixtures defined here are available to
# every test module in this directory (and below) without importing them.
# That is why test_db.py, test_voting.py, and test_api.py can all use store.
#
# Fixtures are setup helpers for tests. When a test function lists a fixture
# name as a parameter, pytest runs that fixture first and passes its result
# into the test. Fixtures can depend on other fixtures, forming a chain.


@pytest.fixture
def aws_credentials(monkeypatch):
    # monkeypatch is a built-in pytest fixture for temporary changes.
    # .setenv sets an environment variable for this test only; pytest
    # restores the old environment afterward.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)


@pytest.fixture
def polls_table(aws_credentials):
    # Naming aws_credentials as a parameter makes pytest run that fixture
    # first (fake AWS env vars), then this one.
    #
    # mock_aws() tells moto to intercept AWS calls in this block so boto3
    # talks to an in-memory fake instead of the real network.
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name=REGION)
        # create_table defines the Polls table inside moto's fake account.
        # BillingMode is required by the API (unless you set provisioned
        # read/write capacity instead).
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "pollId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "pollId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        # create_table returns immediately, but the system behind the scenes is
        # still creating the table. wait_until_exists blocks until it is ready.
        table.wait_until_exists()
        # yield hands the table to the test (or next fixture). Code before
        # yield is setup; after the test finishes, pytest resumes here for
        # cleanup. Exiting the with block then turns off mock_aws.
        yield table


@pytest.fixture
def store(polls_table):
    # Depends on polls_table, which depends on aws_credentials and runs
    # inside mock_aws — so this PollStorage uses moto, not a real database.
    return PollStorage(table_name=TABLE_NAME, region_name=REGION)
