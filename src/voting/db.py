import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import BotoCoreError, ClientError

from voting.poll_types import PollData, item_from_poll_data, poll_data_from_item

# Note on boto3 exceptions:
# ClientError means DynamoDB received the request and returned an error. The
# details are in exc.response["Error"]["Code"] (for example,
# ConditionalCheckFailedException when a ConditionExpression fails).
# BotoCoreError means the call failed before a normal service response
# (connection refused, timeout, DNS failure, and similar).
#
# Most of the time we catch both and turn them into DatabaseUnavailableError.
# Occasionally we must handle ClientError separately first — for example in
# add_poll, where ConditionalCheckFailedException means "poll already exists"
# rather than "database is down."


class DatabaseUnavailableError(Exception):
    """Raised when the database or table cannot be reached."""


class PollAlreadyExistsError(Exception):
    """Raised when adding a poll whose id is already in the table."""


class PollNotFoundError(Exception):
    """Raised when a poll id is not in the table."""


class InvalidOptionError(Exception):
    """Raised when a vote option number is not valid for a poll."""


class PollStorage:
    """Stores and loads polls in DynamoDB.

    Credentials come from the normal AWS chain (env, config file, or
    instance/Lambda role). Pass endpoint_url only when using DynamoDB Local.
    """

    def __init__(
        self,
        table_name: str,
        region_name: str,
        endpoint_url: str | None = None,
    ):
        """Connect to a DynamoDB table.

        table_name: name of the Polls table
        region_name: AWS region (always required)
        endpoint_url: DynamoDB Local URL, or omit for Amazon DynamoDB
        """
        if not table_name:
            raise ValueError("table_name is required")
        if not region_name:
            raise ValueError("region_name is required")

        if endpoint_url is not None:
            resource = boto3.resource(
                "dynamodb",
                region_name=region_name,
                endpoint_url=endpoint_url,
            )
        else:
            resource = boto3.resource(
                "dynamodb",
                region_name=region_name,
            )
        self._table = resource.Table(table_name)

    def ping(self) -> None:
        """Check that the table exists and is ACTIVE.

        Returns normally if the database is usable. Raises
        DatabaseUnavailableError if the connection fails or the table
        is missing / not ready.
        """
        try:
            self._table.load()
        except (BotoCoreError, ClientError) as exc:
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc

        if self._table.table_status != "ACTIVE":
            raise DatabaseUnavailableError(
                f"table {self._table.name!r} is not ACTIVE "
                f"(status={self._table.table_status!r})"
            )

    def clear_all(self) -> None:
        """Delete every poll in the table.

        Not part of the application — used by acceptance tests (and similar
        tooling) to reset the table to a known empty state.

        Raises DatabaseUnavailableError on connection / service failures.
        """
        try:
            scan = self._table.scan(ProjectionExpression="pollId")
            with self._table.batch_writer() as batch:
                for item in scan.get("Items", []):
                    batch.delete_item(Key={"pollId": item["pollId"]})
                while "LastEvaluatedKey" in scan:
                    scan = self._table.scan(
                        ProjectionExpression="pollId",
                        ExclusiveStartKey=scan["LastEvaluatedKey"],
                    )
                    for item in scan.get("Items", []):
                        batch.delete_item(Key={"pollId": item["pollId"]})
        except (BotoCoreError, ClientError) as exc:
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc

    def add_poll(self, poll: PollData) -> None:
        """Store a new poll.

        Raises PollAlreadyExistsError if poll_id is already in the table.
        Raises DatabaseUnavailableError on connection / service failures.
        """
        try:
            self._table.put_item(
                Item=item_from_poll_data(poll),
                ConditionExpression=Attr("pollId").not_exists(),
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise PollAlreadyExistsError(
                    f"poll {poll.poll_id!r} already exists"
                ) from exc
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc
        except BotoCoreError as exc:
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc

    def replace_poll(self, poll: PollData) -> None:
        """Store a poll, overwriting any existing item with the same id.

        Raises DatabaseUnavailableError on connection / service failures.
        """
        try:
            self._table.put_item(Item=item_from_poll_data(poll))
        except (BotoCoreError, ClientError) as exc:
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc

    def get_poll(self, poll_id: str) -> PollData | None:
        """Return one poll by id, or None if it does not exist.

        Raises DatabaseUnavailableError on connection / service failures.
        """
        try:
            response = self._table.get_item(Key={"pollId": poll_id})
        except (BotoCoreError, ClientError) as exc:
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc

        item = response.get("Item")
        if item is None:
            return None
        return poll_data_from_item(item)

    def list_polls(self) -> list[PollData]:
        """Return every poll (unsorted).

        Raises DatabaseUnavailableError on connection / service failures.
        """
        try:
            polls = []
            response = self._table.scan()
            for item in response.get("Items", []):
                polls.append(poll_data_from_item(item))
            # Scan may return pages; keep reading until DynamoDB is done.
            while "LastEvaluatedKey" in response:
                response = self._table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                for item in response.get("Items", []):
                    polls.append(poll_data_from_item(item))
            return polls
        except (BotoCoreError, ClientError) as exc:
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc

    def increment_vote(self, poll_id: str, option: int) -> PollData:
        """Atomically add one vote to an option and return the updated poll.

        Raises PollNotFoundError if the poll does not exist.
        Raises InvalidOptionError if the option number is not on the poll.
        Raises DatabaseUnavailableError on connection / service failures.
        """
        poll = self.get_poll(poll_id)
        if poll is None:
            raise PollNotFoundError(f"poll {poll_id!r} not found")

        option_numbers = [opt["number"] for opt in poll.options]
        if option not in option_numbers:
            raise InvalidOptionError(
                f"option {option} is not valid for poll {poll_id!r}"
            )

        try:
            response = self._table.update_item(
                Key={"pollId": poll_id},
                UpdateExpression="ADD options.#opt.votes :one",
                ExpressionAttributeNames={"#opt": str(option)},
                ExpressionAttributeValues={":one": 1},
                ConditionExpression=Attr("pollId").exists(),
                ReturnValues="ALL_NEW",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise PollNotFoundError(f"poll {poll_id!r} not found") from exc
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc
        except BotoCoreError as exc:
            raise DatabaseUnavailableError(f"database unavailable: {exc}") from exc

        return poll_data_from_item(response["Attributes"])
