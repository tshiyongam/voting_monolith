import sys

from flask import Flask, jsonify, render_template, request

from voting.db import DatabaseUnavailableError, PollStorage
from voting.poll_types import PollQuestion, PollResults, PollSummary
from voting.settings import ensure_settings
from voting.voting import (
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
    VotingApp,
)


def _error(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status


def _summary_json(summary: PollSummary) -> dict:
    return {
        "id": summary.id,
        "question": summary.question,
        "totalVotes": summary.total_votes,
    }


def _question_json(poll: PollQuestion) -> dict:
    return {
        "id": poll.id,
        "question": poll.question,
        "options": poll.options,
        "totalVotes": poll.total_votes,
    }


def _results_json(results: PollResults) -> dict:
    return {
        "id": results.id,
        "question": results.question,
        "totalVotes": results.total_votes,
        "results": results.results,
    }


def create_app(voting_app: VotingApp) -> Flask:
    """Build the Flask app and add routes."""
    app = Flask(__name__)

    @app.get("/")
    def index_page():
        return render_template("index.html")

    @app.get("/create")
    def create_page():
        return render_template("create.html")

    @app.get("/vote")
    def vote_page():
        return render_template("vote.html")

    @app.get("/results")
    def results_page():
        return render_template("results.html")

    @app.get("/health")
    def health():
        try:
            voting_app.health()
        except ServiceUnavailableError:
            return jsonify({"status": "unavailable"}), 503
        return jsonify({"status": "ok"}), 200

    @app.get("/polls")
    def list_polls():
        try:
            summaries = voting_app.list_polls()
        except ServiceUnavailableError:
            return jsonify({"status": "unavailable"}), 503
        return jsonify({"polls": [_summary_json(s) for s in summaries]}), 200

    @app.post("/polls")
    def create_poll():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return _error("BAD_REQUEST", "JSON body required", 400)
        if "question" not in body or "options" not in body:
            return _error(
                "BAD_REQUEST",
                "question and options are required",
                400,
            )
        if not isinstance(body["options"], list):
            return _error("BAD_REQUEST", "options must be a list", 400)

        try:
            poll_id = voting_app.create_poll(body["question"], body["options"])
        except ValidationError as exc:
            return _error("BAD_REQUEST", str(exc), 400)
        except ServiceUnavailableError:
            return jsonify({"status": "unavailable"}), 503

        # 201 Created: success that made a new resource (not a plain 200 OK).
        return jsonify({"id": poll_id}), 201

    @app.get("/polls/<poll_id>")
    def get_poll(poll_id):
        try:
            poll = voting_app.get_poll(poll_id)
        except NotFoundError:
            return _error("POLL_NOT_FOUND", "Poll not found", 404)
        except ServiceUnavailableError:
            return jsonify({"status": "unavailable"}), 503
        return jsonify(_question_json(poll)), 200

    @app.post("/polls/<poll_id>/votes")
    def cast_vote(poll_id):
        raw_option = request.args.get("option")
        if raw_option is None:
            return _error("BAD_REQUEST", "option query parameter is required", 400)
        try:
            option = int(raw_option)
        except ValueError:
            return _error(
                "BAD_REQUEST",
                "option must be an integer between 1 and the number of options for this poll",
                400,
            )

        try:
            results = voting_app.cast_vote(poll_id, option)
        except ValidationError as exc:
            return _error("BAD_REQUEST", str(exc), 400)
        except NotFoundError:
            return _error("POLL_NOT_FOUND", "Poll not found", 404)
        except ServiceUnavailableError:
            return jsonify({"status": "unavailable"}), 503

        return jsonify(_results_json(results)), 200

    @app.get("/polls/<poll_id>/results")
    def get_results(poll_id):
        try:
            results = voting_app.get_results(poll_id)
        except NotFoundError:
            return _error("POLL_NOT_FOUND", "Poll not found", 404)
        except ServiceUnavailableError:
            return jsonify({"status": "unavailable"}), 503
        return jsonify(_results_json(results)), 200

    return app


def launch() -> Flask:
    """Build PollStorage + VotingApp + Flask app from settings (for gunicorn too)."""
    settings = ensure_settings()
    storage = PollStorage(
        table_name=settings["POLLS_TABLE_NAME"],
        region_name=settings["AWS_DEFAULT_REGION"],
        endpoint_url=settings["DYNAMODB_ENDPOINT_URL"],
    )
    try:
        storage.ping()
    except DatabaseUnavailableError as exc:
        raise RuntimeError(
            "Database not reachable. Is DynamoDB Local running? "
            "Is the Polls table created (python scripts/create_table.py)? "
            f"Details: {exc}"
        ) from exc

    return create_app(VotingApp(storage))


if __name__ == "__main__":
    try:
        app = launch()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    app.run(debug=True, port=5000)
