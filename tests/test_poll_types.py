from decimal import Decimal

from voting.poll_types import (
    PollData,
    PollQuestion,
    PollResults,
    PollSummary,
    extract_poll_question,
    extract_poll_results,
    extract_poll_summary,
    item_from_poll_data,
    poll_data_from_item,
)


def test_poll_data_from_item_and_back():
    item = {
        "pollId": "k7m2xq9p",
        "createdAt": "2026-07-28T12:15:00.000Z",
        "question": "Favorite lunch spot on campus?",
        "options": {
            "1": {"text": "Commons", "votes": Decimal(10)},
            "2": {"text": "HUB", "votes": Decimal(21)},
            "4": {"text": "Skip lunch", "votes": Decimal(4)},
            "3": {"text": "Off campus", "votes": Decimal(8)},
        },
    }
    poll = poll_data_from_item(item)
    assert poll == PollData(
        poll_id="k7m2xq9p",
        created_at="2026-07-28T12:15:00.000Z",
        question="Favorite lunch spot on campus?",
        options=[
            {"number": 1, "text": "Commons", "votes": 10},
            {"number": 2, "text": "HUB", "votes": 21},
            {"number": 3, "text": "Off campus", "votes": 8},
            {"number": 4, "text": "Skip lunch", "votes": 4},
        ],
    )
    # Round-trip uses ints in the item (what we write); order of map keys
    # does not matter for equality of the reconstructed PollData.
    assert poll_data_from_item(item_from_poll_data(poll)) == poll


def test_extract_poll_question():
    poll = poll_data_from_item(
        {
            "pollId": "k7m2xq9p",
            "createdAt": "2026-07-28T12:15:00.000Z",
            "question": "Favorite lunch spot on campus?",
            "options": {
                "1": {"text": "Commons", "votes": 10},
                "2": {"text": "HUB", "votes": 21},
                "3": {"text": "Off campus", "votes": 8},
                "4": {"text": "Skip lunch", "votes": 4},
            },
        }
    )
    assert extract_poll_question(poll) == PollQuestion(
        id="k7m2xq9p",
        question="Favorite lunch spot on campus?",
        options=[
            {"number": 1, "text": "Commons"},
            {"number": 2, "text": "HUB"},
            {"number": 3, "text": "Off campus"},
            {"number": 4, "text": "Skip lunch"},
        ],
        total_votes=43,
    )


def test_extract_poll_results():
    poll = poll_data_from_item(
        {
            "pollId": "k7m2xq9p",
            "createdAt": "2026-07-28T12:15:00.000Z",
            "question": "Favorite lunch spot on campus?",
            "options": {
                "1": {"text": "Commons", "votes": 10},
                "2": {"text": "HUB", "votes": 21},
                "3": {"text": "Off campus", "votes": 8},
                "4": {"text": "Skip lunch", "votes": 4},
            },
        }
    )
    assert extract_poll_results(poll) == PollResults(
        id="k7m2xq9p",
        question="Favorite lunch spot on campus?",
        results=[
            {"number": 1, "text": "Commons", "votes": 10},
            {"number": 2, "text": "HUB", "votes": 21},
            {"number": 3, "text": "Off campus", "votes": 8},
            {"number": 4, "text": "Skip lunch", "votes": 4},
        ],
        total_votes=43,
    )


def test_extract_poll_summary():
    poll = PollData(
        poll_id="n4w8rt3c",
        created_at="2026-07-20T09:00:00.000Z",
        question="Should the library extend weekend hours?",
        options=[
            {"number": 1, "text": "Yes", "votes": 17},
            {"number": 2, "text": "No", "votes": 6},
        ],
    )
    assert extract_poll_summary(poll) == PollSummary(
        id="n4w8rt3c",
        question="Should the library extend weekend hours?",
        total_votes=23,
    )
