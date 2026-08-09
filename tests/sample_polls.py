"""Named sample polls for tests (and shared with seed / manual checks).

Loaded from data/sample-data.json. Canonical description of each
poll lives in the specs repository sample-data doc (copy JSON into each
version repo; no formal drift CI — keep them in sync by hand).

What each poll is for:

  MEETUP_NO_VOTES  — brand-new poll, all votes 0; newest createdAt
  LUNCH_SPOT       — realistic vote spread (good default for vote tests)
  LIBRARY_HOURS    — minimum of two options
  STUDY_SPOT       — maximum of six options
  CS_MONITOR       — clear leading option
"""

import json
from pathlib import Path

from voting.poll_types import (
    extract_poll_question,
    extract_poll_results,
    extract_poll_summary,
    poll_data_from_item,
)

_SAMPLE_DATA_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "sample-data.json"
)


def _load_items_by_id() -> dict:
    with _SAMPLE_DATA_PATH.open(encoding="utf-8") as handle:
        items = json.load(handle)
    return {item["pollId"]: item for item in items}


def _bundle(item: dict):
    poll_data = poll_data_from_item(item)
    return (
        poll_data,
        extract_poll_question(poll_data),
        extract_poll_results(poll_data),
        extract_poll_summary(poll_data),
    )


_items = _load_items_by_id()

(
    MEETUP_NO_VOTES_POLLDATA,
    MEETUP_NO_VOTES_POLLQUESTION,
    MEETUP_NO_VOTES_POLLRESULTS,
    MEETUP_NO_VOTES_POLLSUMMARY,
) = _bundle(_items["m3n8kp2w"])

(
    LUNCH_SPOT_POLLDATA,
    LUNCH_SPOT_POLLQUESTION,
    LUNCH_SPOT_POLLRESULTS,
    LUNCH_SPOT_POLLSUMMARY,
) = _bundle(_items["k7m2xq9p"])

(
    LIBRARY_HOURS_POLLDATA,
    LIBRARY_HOURS_POLLQUESTION,
    LIBRARY_HOURS_POLLRESULTS,
    LIBRARY_HOURS_POLLSUMMARY,
) = _bundle(_items["n4w8rt3c"])

(
    STUDY_SPOT_POLLDATA,
    STUDY_SPOT_POLLQUESTION,
    STUDY_SPOT_POLLRESULTS,
    STUDY_SPOT_POLLSUMMARY,
) = _bundle(_items["p9q4vs1b"])

(
    CS_MONITOR_POLLDATA,
    CS_MONITOR_POLLQUESTION,
    CS_MONITOR_POLLRESULTS,
    CS_MONITOR_POLLSUMMARY,
) = _bundle(_items["r2t7yh5d"])

ALL_SAMPLE_POLLDATA = [
    MEETUP_NO_VOTES_POLLDATA,
    LUNCH_SPOT_POLLDATA,
    LIBRARY_HOURS_POLLDATA,
    STUDY_SPOT_POLLDATA,
    CS_MONITOR_POLLDATA,
]
