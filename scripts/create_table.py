"""Create the Polls table in DynamoDB (table must be reachable via .env)."""

import sys

import boto3
from botocore.exceptions import ClientError

from voting.settings import ensure_settings


def _ask_replace_or_quit(table_name: str) -> str:
    while True:
        answer = input(
            f"Table {table_name!r} already exists. "
            "[r]eplace (deletes all data) or [q]uit? "
        ).strip().lower()
        if answer in ("r", "replace"):
            return "replace"
        if answer in ("q", "quit"):
            return "quit"
        print("Please enter r or q.")


def _table_exists(dynamodb, table_name: str) -> bool:
    try:
        dynamodb.meta.client.describe_table(TableName=table_name)
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        raise


def _create_table(dynamodb, table_name: str) -> None:
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "pollId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "pollId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print(f"Created table {table_name!r}.")


def _delete_table(dynamodb, table_name: str) -> None:
    table = dynamodb.Table(table_name)
    table.delete()
    table.wait_until_not_exists()
    print(f"Deleted table {table_name!r}.")


def create_polls_table(
    table_name: str, region_name: str, endpoint_url: str
) -> None:
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=region_name,
        endpoint_url=endpoint_url,
    )

    if _table_exists(dynamodb, table_name):
        choice = _ask_replace_or_quit(table_name)
        if choice == "quit":
            print("Table creation stopped.")
            sys.exit(1)
        _delete_table(dynamodb, table_name)

    _create_table(dynamodb, table_name)


def main() -> None:
    try:
        settings = ensure_settings()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    create_polls_table(
        settings["POLLS_TABLE_NAME"],
        settings["AWS_DEFAULT_REGION"],
        settings["DYNAMODB_ENDPOINT_URL"],
    )


if __name__ == "__main__":
    main()
