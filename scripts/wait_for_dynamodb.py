"""Wait until DynamoDB answers ListTables (CI and systemd ExecStartPre)."""

import argparse
import sys
import time

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from voting.settings import ensure_settings


def wait_for_dynamodb(
    region_name: str,
    endpoint_url: str,
    timeout_seconds: int,
) -> None:
    client = boto3.client(
        "dynamodb",
        region_name=region_name,
        endpoint_url=endpoint_url,
        config=Config(
            connect_timeout=1,
            read_timeout=1,
            retries={"max_attempts": 1},
        ),
    )
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            client.list_tables()
            return
        except (BotoCoreError, ClientError, OSError):
            time.sleep(1)
    raise TimeoutError(
        f"DynamoDB did not become ready within {timeout_seconds}s "
        f"(endpoint {endpoint_url!r})."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wait until DynamoDB responds to ListTables."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Seconds to wait before failing (default: 60).",
    )
    args = parser.parse_args()

    try:
        settings = ensure_settings()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    try:
        wait_for_dynamodb(
            settings["AWS_DEFAULT_REGION"],
            settings["DYNAMODB_ENDPOINT_URL"],
            args.timeout,
        )
    except TimeoutError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    print("DynamoDB is ready.")


if __name__ == "__main__":
    main()
