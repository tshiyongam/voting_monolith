# Design

This project is a single web application: one process serves the HTTP API and the browser UI, and DynamoDB Local on your machine holds poll data.

## Data representations

In DynamoDB, a poll is one item:

```json
{
  "pollId": "k7m2xq9p",
  "createdAt": "2026-07-28T12:15:00.000Z",
  "question": "Favorite lunch spot on campus?",
  "options": {
    "1": { "text": "Commons", "votes": 10 },
    "2": { "text": "HUB", "votes": 21 },
    "3": { "text": "Off campus", "votes": 8 },
    "4": { "text": "Skip lunch", "votes": 4 }
  }
}
```

**`PollData`** is the same information as a Python object, with options as an ordered list:

```python
PollData(
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
```

**`PollQuestion`** is a poll question a user is going to vote on: id, question, option numbers and text, and total votes — without per-option counts.

```python
PollQuestion(
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
```

**`PollResults`** is the results of a poll: id, question, each option with its vote count, and total votes.

```python
PollResults(
    id="k7m2xq9p",
    question="Favorite lunch spot on campus?",
    total_votes=43,
    results=[
        {"number": 1, "text": "Commons", "votes": 10},
        {"number": 2, "text": "HUB", "votes": 21},
        {"number": 3, "text": "Off campus", "votes": 8},
        {"number": 4, "text": "Skip lunch", "votes": 4},
    ],
)
```

**`PollSummary`** is a short listing entry for a poll: id, question, and total votes.

```python
PollSummary(
    id="k7m2xq9p",
    question="Favorite lunch spot on campus?",
    total_votes=43,
)
```

## Layers

The code is organized in three layers:

1. **API** — handles HTTP: parse requests, call the application, return responses.
2. **Application** — handles business logic: the rules and workflows of voting.
3. **DB** — interacts with the database: turn application requests into DynamoDB operations and turn DynamoDB results into data the application can use.

### API

Handles HTTP requests and response messages; talks to the application layer.

- Accept requests to list polls, create a poll, get a poll to vote on, cast a vote, get results, and check health.
- Check that required fields are present and have the right types (for example, that `option` is an integer in 1..6).
- Call the matching application operation.
- Return JSON: poll id on create (`201`); map `PollQuestion`, `PollResults`, and `PollSummary` to camelCase JSON for the OpenAPI contract (Python uses snake_case field names). Flask lives in `voting.app.create_app`; application logic lives in `voting.voting.VotingApp`.
- Health: `200` and `{"status": "ok"}` when the application health check succeeds; `503` and `{"status": "unavailable"}` when it fails (process is up, database is not usable).
- Map other application errors to HTTP status codes and the standard error JSON body.
- Serve the static HTML, CSS, and JavaScript UI.

### Application

Works in terms of **`PollData`**, **`PollQuestion`**, **`PollResults`**, and **`PollSummary`**.

- `create_poll(question: str, option_texts: list[str]) -> str` — trim and validate input; assign `poll_id` and `created_at`; build `PollData` with zero votes; store it; return the new poll id.
- `list_polls() -> list[PollSummary]` — retrieve all `PollData` from the database; sort newest first; extract a `PollSummary` for each poll.
- `get_poll(poll_id: str) -> PollQuestion` — retrieve a `PollData` from the database and extract a `PollQuestion`; raise an exception if the poll is missing.
- `get_results(poll_id: str) -> PollResults` — retrieve a `PollData` from the database and extract a `PollResults`; raise an exception if the poll is missing.
- `cast_vote(poll_id: str, option: int) -> PollResults` — validate that the option is valid for this poll; tell the database to increment that option; construct the `PollResults`.
- `health()` — check that the database is reachable; raise an exception if not (API maps that to HTTP `503`).

Errors generate exceptions that the API layer converts to HTTP responses.

### DB

Works in terms of DynamoDB items and **`PollData`**. The type is **`PollStorage`**.

- Convert a DynamoDB item to `PollData`, and `PollData` to a DynamoDB item.
- `add_poll(poll: PollData) -> None` — store a new poll; raise an exception if a poll with that id already exists.
- `replace_poll(poll: PollData) -> None` — store a poll, overwriting any existing item with the same id (used by the seed script).
- `get_poll(poll_id: str) -> PollData | None` — load one poll by id.
- `list_polls() -> list[PollData]` — return every poll (unsorted).
- `increment_vote(poll_id: str, option: int) -> PollData` — atomically add one vote to that option and return the updated `PollData`; raise an exception if the poll is missing or the option is not valid for that poll.
- `ping() -> None` — confirm the database and table are reachable; raise an exception if not.
- `clear_all() -> None` — delete every poll. Not part of the application UI; used by acceptance tests (and similar tooling) to reset the table.

## UI

The browser UI is vanilla HTML, CSS, and JavaScript. It calls the HTTP API with `fetch`.

- Create and vote forms validate input in the page before submitting; the server validates again.
- After a successful create, the UI reads the returned poll id and navigates to the vote page for that poll. The vote page loads `PollQuestion` with `GET /polls/{id}`.
- List rows use each `PollSummary` id for Vote and Results navigation.

## Sample data and seeding

Poll fixtures live in `data/sample-data.json` (kept in sync by hand with the specs repository fixture). See [development.md](development.md) and [dynamodb-local.md](dynamodb-local.md). `scripts/create_table.py` creates the `Polls` table (fails if it already exists); `scripts/delete_table.py` removes it (prompts unless `-y`); optional `scripts/seed.py` loads the sample file (and fails if the table is missing).

For local manual testing: start DynamoDB Local, create the table, optionally seed, run `python -m voting.app`, use the browser.

## Testing

### Unit and layer tests

Unit and layer tests under `tests/` use **moto** to provide an in-process DynamoDB stand-in. Tests create the table (and seed when useful), then exercise the DB layer and higher layers through real **boto3** calls. No separate database process is required for `pytest`.

### Acceptance tests

Acceptance tests under `tests_ui/` use **Playwright** against a real browser. DynamoDB Local and the Flask app must already be running on the usual ports. The suite checks `/health` at startup and uses `PollStorage` fixtures (including `clear_all`) to arrange table data. See [development.md](development.md).

### Lint

**Ruff** (`ruff check src tests scripts tests_ui`) is the linter. Keep the tree clean before committing.

### CI (GitHub Actions)

Default checks install Python deps (including moto and ruff), then run `ruff check` and unit `pytest`. No external database process.

An optional **Acceptance tests** workflow (`workflow_dispatch`) starts DynamoDB Local as an Actions service container, creates the table, starts the app, and runs `pytest tests_ui`.

## Config

`ensure_settings()` in `voting.settings` loads `.env` (if present) and requires the DynamoDB-related environment variables. `launch()` builds `PollStorage`, pings the table, and creates the Flask app. Scripts and acceptance fixtures call `ensure_settings` the same way. On EC2, gunicorn loads the app with `'voting.app:launch()'`.

## Deploy on EC2

See [deploy-ec2.md](deploy-ec2.md). One root script (`deploy/userdata.sh`) deploys to `/home/ec2-user/voting_monolith`: clone, venv, `.env`, DynamoDB Local on disk, systemd units, create `Polls` table, gunicorn on port 80 (two workers by default). Long-running units run as `ec2-user`; `voting.service` waits for DynamoDB before starting.

## Package layout

```
.
  README.md
  docs/
    development.md   # local Python / test / run workflow
    dynamodb-local.md
    deploy-ec2.md    # EC2 manual install + user data
    design.md        # this file
  config/
    example.env      # copy to .env at project root
  data/
    sample-data.json # copy of specs fixture; seed + tests (keep in sync by hand)
  db/                # DynamoDB Local JAR + data (gitignored)
  deploy/
    dynamodb-local.service
    voting.service
    userdata.sh           # root EC2 bootstrap (set REPO_URL; push before CFN)
    cloudformation.yaml   # EC2 + SG; UserData stub curls userdata.sh from your fork

  .env               # local settings (gitignored; create from example.env)
  setup.py
  scripts/
    create_table.py       # create Polls table (fails if it exists)
    delete_table.py       # delete Polls table (prompt, or -y)
    wait_for_dynamodb.py  # poll ListTables until ready (CI + systemd)
    seed.py               # load data/sample-data.json (table must exist)
  src/voting/
    settings.py      # ensure_settings() — load .env, require keys
    poll_types.py    # PollData / views + item + extract helpers
    db.py            # PollStorage (boto3)
    voting.py        # VotingApp
    app.py           # Flask create_app + launch
    templates/       # HTML pages (render_template)
    static/          # CSS (and other static assets)
  tests/
    conftest.py      # shared moto / PollStorage fixtures
    sample_polls.py  # named constants from data/sample-data.json
    test_poll_types.py
    test_db.py
    test_voting.py
    test_api.py
  tests_ui/          # Playwright acceptance (running app + DynamoDB Local)
    conftest.py      # /health gate, base_url, data fixtures
    test_browse_empty.py
    test_browse.py
    test_create.py
    test_vote.py
    test_results.py
```
