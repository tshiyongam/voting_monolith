"""Create the Polls table in DynamoDB (table must be reachable via .env).

Fails if the table already exists. To reset, run delete_table.py first.
"""

import sys

import boto3
from botocore.exceptions import ClientError

from voting.settings import ensure_settings


def _table_exists(dynamodb, table_name: str) -> bool:
    try:
        dynamodb.meta.client.describe_table(TableName=table_name)
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        raise


def main() -> None:
    try:
        settings = ensure_settings()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    table_name = settings["POLLS_TABLE_NAME"]
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=settings["AWS_DEFAULT_REGION"],
        endpoint_url=settings["DYNAMODB_ENDPOINT_URL"],
    )

    if _table_exists(dynamodb, table_name):
        print(
            f"Table {table_name!r} already exists. "
            "Delete it first if you want to recreate: "
            "python scripts/delete_table.py",
            file=sys.stderr,
        )
        sys.exit(1)

    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "pollId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "pollId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()


if __name__ == "__main__":
    main()
