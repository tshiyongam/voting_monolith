# Polls

This is the monolithic implementation of the Voting application. See the **specs** repository for the product specifications (use cases, API, data model, and related materials).

**Monolithic** here means Flask (HTTP API and browser UI) and DynamoDB run together on a single machine.

## Documentation

| Doc | Contents |
|-----|----------|
| [Development setup](docs/development.md) | Virtualenv, install, unit tests, lint, `.env`, DynamoDB Local, run the app, acceptance tests |
| [DynamoDB Local](docs/dynamodb-local.md) | Download, install into `db/`, start command, flags, port |
| [Deploy on EC2](docs/deploy-ec2.md) | Security group, manual install, user data, systemd units |
| [Design](docs/design.md) | Layers, data types, UI notes, package layout |

## Quick start

- Create a virtual environment and install dependencies
- Configure `.env` from `config/example.env`
- Start DynamoDB Local and create the `Polls` table
- Run `python -m voting.app` and open [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

See [Development setup](docs/development.md) for full steps.
