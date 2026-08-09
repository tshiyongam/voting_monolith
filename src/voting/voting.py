import secrets
from datetime import datetime, timezone

from voting.db import (
    DatabaseUnavailableError,
    InvalidOptionError,
    PollAlreadyExistsError,
    PollNotFoundError,
    PollStorage,
)
from voting.poll_types import (
    PollData,
    PollQuestion,
    PollResults,
    PollSummary,
    extract_poll_question,
    extract_poll_results,
    extract_poll_summary,
)


class ValidationError(Exception):
    """Raised when input fails application rules (create, vote option, etc.)."""


class NotFoundError(Exception):
    """Raised when a poll id does not exist."""


class ServiceUnavailableError(Exception):
    """Raised when the data store cannot be reached.

    Wraps the DB layer's DatabaseUnavailableError so callers (the API) do
    not need to import from voting.db.
    """


class VotingApp:
    """Application logic for polls. Construct with a PollStorage; call health() at launch."""

    def __init__(self, poll_storage: PollStorage):
        self._store = poll_storage

    def health(self) -> None:
        """Check that the store is reachable.

        Raises ServiceUnavailableError if the database is not usable.
        """
        try:
            self._store.ping()
        except DatabaseUnavailableError as exc:
            raise ServiceUnavailableError(
                "service unavailable: database not reachable"
            ) from exc

    def create_poll(self, question: str, option_texts: list[str]) -> str:
        """Validate input, store a new poll with zero votes, return its id."""
        question = question.strip()
        options = [text.strip() for text in option_texts]

        if not question:
            raise ValidationError("question must not be blank")
        if len(question) > 280:
            raise ValidationError("question must be at most 280 characters")
        if len(options) < 2 or len(options) > 6:
            raise ValidationError("polls need between 2 and 6 options")
        for text in options:
            if not text:
                raise ValidationError("option labels must not be blank")
            if len(text) > 100:
                raise ValidationError("option labels must be at most 100 characters")
        if len(set(options)) != len(options):
            raise ValidationError("option labels must be distinct")

        # Opaque random id: not sequential, so clients cannot infer how many
        # polls exist or guess the next id. secrets.token_hex(4) → 8 hex chars.
        poll_id = secrets.token_hex(4)
        created_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

        poll = PollData(
            poll_id=poll_id,
            created_at=created_at,
            question=question,
            options=[
                {"number": i, "text": text, "votes": 0}
                for i, text in enumerate(options, start=1)
            ],
        )
        try:
            self._store.add_poll(poll)
        except PollAlreadyExistsError as exc:
            raise ServiceUnavailableError(
                "service unavailable: poll id collision"
            ) from exc
        except DatabaseUnavailableError as exc:
            raise ServiceUnavailableError(
                "service unavailable: database not reachable"
            ) from exc
        return poll_id

    def list_polls(self) -> list[PollSummary]:
        """Return all polls as summaries, newest first."""
        try:
            polls = self._store.list_polls()
        except DatabaseUnavailableError as exc:
            raise ServiceUnavailableError(
                "service unavailable: database not reachable"
            ) from exc

        polls = sorted(polls, key=lambda p: p.created_at, reverse=True)
        return [extract_poll_summary(p) for p in polls]

    def get_poll(self, poll_id: str) -> PollQuestion:
        """Return a poll for voting, or raise NotFoundError."""
        poll = self._load_poll(poll_id)
        return extract_poll_question(poll)

    def get_results(self, poll_id: str) -> PollResults:
        """Return tallies for a poll, or raise NotFoundError."""
        poll = self._load_poll(poll_id)
        return extract_poll_results(poll)

    def cast_vote(self, poll_id: str, option: int) -> PollResults:
        """Record one vote and return updated results."""
        poll = self._load_poll(poll_id)
        option_numbers = [opt["number"] for opt in poll.options]
        if option not in option_numbers:
            raise ValidationError(f"option {option} is not valid for this poll")

        try:
            updated = self._store.increment_vote(poll_id, option)
        except PollNotFoundError as exc:
            raise NotFoundError(f"poll {poll_id!r} not found") from exc
        except InvalidOptionError as exc:
            raise ValidationError(str(exc)) from exc
        except DatabaseUnavailableError as exc:
            raise ServiceUnavailableError(
                "service unavailable: database not reachable"
            ) from exc

        return extract_poll_results(updated)

    def _load_poll(self, poll_id: str) -> PollData:
        try:
            poll = self._store.get_poll(poll_id)
        except DatabaseUnavailableError as exc:
            raise ServiceUnavailableError(
                "service unavailable: database not reachable"
            ) from exc
        if poll is None:
            raise NotFoundError(f"poll {poll_id!r} not found")
        return poll
