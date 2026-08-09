# Local development setup

How to run this project on your laptop: Python environment, tests, lint, DynamoDB Local, and the web app.

For DynamoDB Local install/start details, see [dynamodb-local.md](dynamodb-local.md).

## 1. Create a virtual environment

From the root of the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install libraries

```bash
pip install -r requirements.txt
pip install -e .
```

The editable install (`-e .`) makes the `voting` package importable while you edit source under `src/voting/`.

## 3. Run tests

With the venv active:

```bash
pytest
```

Unit tests use **moto** (an in-process fake DynamoDB). You do **not** need DynamoDB Local running for `pytest`.

## 4. Run the linter

```bash
ruff check src tests scripts tests_ui
```

Fix reported issues before you commit.

## 5. Configure `.env`

Copy the example file and adjust if needed:

```bash
cp config/example.env .env
```

`.env` holds AWS credentials and DynamoDB configuration for local runs. Keep it out of git (it is listed in `.gitignore`).

Required keys are documented in `config/example.env`. For DynamoDB Local you will set the endpoint to `http://localhost:8000` and use dummy AWS keys.

## 6. Start DynamoDB Local

```bash
cd db
java --enable-native-access=ALL-UNNAMED -jar DynamoDBLocal.jar -sharedDb -inMemory
```

Leave that process running. See [dynamodb-local.md](dynamodb-local.md) for download, install into `db/`, flags, and port notes.

## 7. Create the Polls table

With the venv active, DynamoDB Local up, and `.env` in place:

```bash
python scripts/create_table.py
```

If DynamoDB Local was started with `-inMemory` and you restart it, run this again (the table does not survive the process).

## 8. Seed sample data (optional)

The app works with an empty `Polls` table. Seed only if you want the sample polls from `data/sample-data.json`.

With the venv active, DynamoDB Local up, `.env` in place, and the table already created:

```bash
python scripts/seed.py
```

If the table is missing, the script exits with an error telling you to run `create_table.py` first.

## 9. Launch the web app

With the venv active, DynamoDB Local running, and the `Polls` table present:

```bash
python -m voting.app
```

The server listens on port **5000**. Open:

[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## 10. Run acceptance tests (Playwright)

Unit tests (`pytest`) use `moto` and do **not** need DynamoDB Local. Acceptance tests drive a real browser against the app you already started on port **5000**.

One-time browser install:

```bash
playwright install chromium
```

With DynamoDB Local running, the `Polls` table created, and the web app up:

```bash
pytest tests_ui
```

The suite checks `http://127.0.0.1:5000/health` once at startup and stops immediately if the app is not healthy. Individual tests reset table data as needed (they do not start DynamoDB Local or Flask for you).
