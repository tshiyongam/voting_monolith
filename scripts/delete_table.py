"""Delete the Polls table in DynamoDB (table must be reachable via .env).

Prompts for confirmation unless -y is passed.
"""

import argparse
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


def _confirm_delete(table_name: str) -> bool:
    answer = input(
        f"Delete table {table_name!r}? This cannot be undone. [y/N] "
    ).strip().lower()
    return answer in ("y", "yes")


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete the Polls DynamoDB table.")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Delete without prompting.",
    )
    args = parser.parse_args()

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

    if not _table_exists(dynamodb, table_name):
        print(f"Table {table_name!r} does not exist.", file=sys.stderr)
        sys.exit(1)

    if not args.yes and not _confirm_delete(table_name):
        print("Delete cancelled.")
        sys.exit(1)

    table = dynamodb.Table(table_name)
    table.delete()
    table.wait_until_not_exists()
    print(f"Deleted table {table_name!r}.")


if __name__ == "__main__":
    main()
