"""Load data/sample-data.json into the Polls table (table must already exist)."""

import json
import sys
from pathlib import Path

from voting.db import (
    DatabaseUnavailableError,
    PollAlreadyExistsError,
    PollStorage,
)
from voting.poll_types import poll_data_from_item
from voting.settings import ensure_settings

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_PATH = ROOT / "data" / "sample-data.json"


def _ask_replace_or_quit(poll_id: str) -> str:
    while True:
        answer = input(
            f"Poll {poll_id!r} already exists. [r]eplace or [q]uit? "
        ).strip().lower()
        if answer in ("r", "replace"):
            return "replace"
        if answer in ("q", "quit"):
            return "quit"
        print("Please enter r or q.")


def seed_polls(storage: PollStorage) -> None:
    with SAMPLE_DATA_PATH.open(encoding="utf-8") as handle:
        items = json.load(handle)

    loaded = 0
    replaced = 0
    for item in items:
        poll = poll_data_from_item(item)
        try:
            storage.add_poll(poll)
            loaded += 1
            print(f"  loaded {poll.poll_id}")
        except PollAlreadyExistsError:
            choice = _ask_replace_or_quit(poll.poll_id)
            if choice == "quit":
                print("Seeding stopped.")
                print(f"Done. loaded={loaded} replaced={replaced}")
                sys.exit(1)
            storage.replace_poll(poll)
            replaced += 1
            print(f"  replaced {poll.poll_id}")

    print(f"Done. loaded={loaded} replaced={replaced}")


def main() -> None:
    try:
        settings = ensure_settings()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    storage = PollStorage(
        table_name=settings["POLLS_TABLE_NAME"],
        region_name=settings["AWS_DEFAULT_REGION"],
        endpoint_url=settings["DYNAMODB_ENDPOINT_URL"],
    )
    try:
        storage.ping()
    except DatabaseUnavailableError as exc:
        print(
            "Polls table is missing or unreachable. "
            "Create it first: python scripts/create_table.py\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Seeding from {SAMPLE_DATA_PATH} …")
    seed_polls(storage)


if __name__ == "__main__":
    main()
