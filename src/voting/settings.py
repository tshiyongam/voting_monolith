"""Load .env and require the settings this project needs to reach DynamoDB."""

import os

from dotenv import load_dotenv

REQUIRED_SETTINGS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_DEFAULT_REGION",
    "POLLS_TABLE_NAME",
    "DYNAMODB_ENDPOINT_URL",
)


def ensure_settings() -> dict[str, str]:
    """Load .env (if present) and require DynamoDB-related settings.

    Returns a dict of the required values. If this returns, every key in
    REQUIRED_SETTINGS is set in the environment (and in the returned dict).

    Raises RuntimeError if any required setting is missing.
    """
    load_dotenv()
    missing = [name for name in REQUIRED_SETTINGS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "Missing required settings in the environment / .env: "
            + ", ".join(missing)
        )
    return {name: os.environ[name] for name in REQUIRED_SETTINGS}
