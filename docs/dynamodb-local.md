# DynamoDB Local

This project runs [DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html) locally on your laptop. boto3 reaches it on port **8000**.

## Download and install

1. Create a `db/` folder at the root of the project.
2. Download the DynamoDB Local archive from the page linked above (use the download link on that page).
3. Extract the archive into `db/`. When you are done, `db/` should contain `DynamoDBLocal.jar` and a `DynamoDBLocal_lib` folder (among other files from the archive).

`DynamoDBLocal_lib` holds native libraries DynamoDB Local needs at startup. Keep the JAR and that folder together in `db/`. Any on-disk database files DynamoDB Local creates also land in `db/` when you start it from there. The project `.gitignore` ignores all of `db/`, so none of this is committed.

For more information, see the page linked at the top of this document.

## Start DynamoDB Local

From the project root:

```bash
cd db
java --enable-native-access=ALL-UNNAMED -jar DynamoDBLocal.jar -sharedDb -inMemory
```

Leave that process running. Stop the process (Ctrl+C) to shut down the database.

The command includes these switches:

- **`--enable-native-access=ALL-UNNAMED`** — Lets DynamoDB Local load its native SQLite library under current Java rules. Without this, Java prints a warning (and may refuse the load in a future release).
- **`-sharedDb`** — Use one shared database for every client, regardless of which access key or region string they send. Without this, each set of credentials gets a separate empty database, and it is easy to think your table “disappeared.”
- **`-inMemory`** — Keep data in memory only. When you stop the process, all data is gone, so you will need to create the table again (and re-seed if you use sample data) the next time you start.

DynamoDB Local listens on port **8000**. If something else on your laptop already uses 8000, free that port before starting.

## Create the table and (optionally) seed data

With your virtual environment active and DynamoDB Local running:

```bash
python scripts/create_table.py
```

To load the sample polls from `data/sample-data.json` (optional; the table must already exist):

```bash
python scripts/seed.py
```
