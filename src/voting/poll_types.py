from dataclasses import dataclass
from decimal import Decimal

# boto3 / DynamoDB use plain dicts (attribute names like "pollId").
# These dataclasses are the Pythonic shapes we pass through the app
# (poll.question instead of poll["question"]).
#
# frozen=True prevents reassigning fields (poll.question = "..."). Nested
# option dicts/lists can still be mutated in place — keep that in mind.
# Full deep immutability would mean frozen option types as well (for example
# PollOption with number/text/votes, and PollQuestionOption with only
# number/text), stored in a tuple instead of a list so callers cannot
# append or replace entries. PollData and PollResults could share the
# same PollOption type. We skip that here so the example stays smaller:
# list[dict] for options is enough for this project.


@dataclass(frozen=True)
class PollData:
    """Full poll as stored and returned by the DB layer."""

    poll_id: str
    created_at: str
    question: str
    options: list[dict]
    # each option: {"number": int, "text": str, "votes": int}


@dataclass(frozen=True)
class PollQuestion:
    """Poll as shown when voting (no per-option vote counts)."""

    id: str
    question: str
    options: list[dict]
    # each option: {"number": int, "text": str}
    total_votes: int


@dataclass(frozen=True)
class PollResults:
    """Poll tallies for the results view."""

    id: str
    question: str
    results: list[dict]
    # each result: {"number": int, "text": str, "votes": int}
    total_votes: int


@dataclass(frozen=True)
class PollSummary:
    """Short listing entry for a poll."""

    id: str
    question: str
    total_votes: int


# --- DynamoDB item <-> PollData (DB boundary) ---


def item_from_poll_data(poll: PollData) -> dict:
    """Convert PollData to a DynamoDB item dict."""
    options = {}
    for opt in poll.options:
        options[str(opt["number"])] = {
            "text": opt["text"],
            "votes": opt["votes"],
        }
    return {
        "pollId": poll.poll_id,
        "createdAt": poll.created_at,
        "question": poll.question,
        "options": options,
    }


def poll_data_from_item(item: dict) -> PollData:
    """Convert a DynamoDB item dict to PollData."""
    options = []
    for key in sorted(item["options"].keys(), key=int):
        opt = item["options"][key]
        votes = opt["votes"]
        # DynamoDB returns numbers as Decimal; store votes as int.
        if isinstance(votes, Decimal):
            votes = int(votes)
        options.append(
            {
                "number": int(key),
                "text": opt["text"],
                "votes": int(votes),
            }
        )
    return PollData(
        poll_id=item["pollId"],
        created_at=item["createdAt"],
        question=item["question"],
        options=options,
    )


# --- PollData -> view types (application projections) ---


def _total_votes(poll: PollData) -> int:
    return sum(opt["votes"] for opt in poll.options)


def extract_poll_question(poll: PollData) -> PollQuestion:
    """Build a PollQuestion view from PollData (hides per-option votes)."""
    options = [{"number": opt["number"], "text": opt["text"]} for opt in poll.options]
    return PollQuestion(
        id=poll.poll_id,
        question=poll.question,
        options=options,
        total_votes=_total_votes(poll),
    )


def extract_poll_results(poll: PollData) -> PollResults:
    """Build a PollResults view from PollData."""
    results = [
        {
            "number": opt["number"],
            "text": opt["text"],
            "votes": opt["votes"],
        }
        for opt in poll.options
    ]
    return PollResults(
        id=poll.poll_id,
        question=poll.question,
        results=results,
        total_votes=_total_votes(poll),
    )


def extract_poll_summary(poll: PollData) -> PollSummary:
    """Build a PollSummary view from PollData."""
    return PollSummary(
        id=poll.poll_id,
        question=poll.question,
        total_votes=_total_votes(poll),
    )
