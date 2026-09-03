# Design

This document describes the design of the Flask server and how data moves through its various layers.  The web API and database are *delivery mechansims for the core application, and there is one layer for each:

1. **API** — handles HTTP: parse requests, call the application, return responses.
2. **Application** — handles business logic: the rules and workflows of voting.
3. **DB** — interacts with the database: turn application requests into DynamoDB operations and turn DynamoDB results into data the application can use.


![Arch](arch.png)



## Data representations

The data for this application is a collection of polls.  This section describes how this data is stored in the database and the various types used to pass data around within the Flask server.

The database layer queries the database to retrieve **all** the information about a poll.  The application layer extracts the necessary information for the request.  The API layer takes the data and translates it into an HTTP reponse message.

### Database Representation


Within the database, we store all the data for a single poll together.  Each poll has an ID, creation date, question, and list of options (each of which has a number of votes).

For example, here is a single poll:

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

The database is made up of a collection of polls.



### Raw Query Result

The Python type **`PollData`** is used to hold the result of a query.  The names and values of the fields match the data in the database exactly:

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

### Poll Summary

When the user views the list of available polls, for each poll they see the question text and the total number of votes, but they do not see the options.  The Python type **`PollSummary`** holds the information used for this view:


```python
PollSummary(
    id="k7m2xq9p",
    question="Favorite lunch spot on campus?",
    total_votes=43,
)
```



### Poll Question


When a user votes on a poll, they see the question text, the options, and the total number of votes.  They do NOT see the number of votes for each option.  The Python type **`PollQuestion`**  holds the information used for this view:

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


### Poll Reults

When the user views the results of a poll, they see the question text, each of the options with the number of votes it received, and the total number of votes.  The Python type **`PollResults`** holds the information used for this view:

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
