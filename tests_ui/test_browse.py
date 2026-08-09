"""Browse polls when the table already has data."""


def test_list_shows_poll_question_and_vote_total(page, lunch_spot_poll):
    # page: pytest-playwright browser page.
    # lunch_spot_poll: sample poll loaded into an otherwise empty table.
    page.goto("/")

    row = page.locator(".poll-row").filter(
        has_text=lunch_spot_poll.question
    )
    row.wait_for()
    assert row.get_by_text("43 votes").is_visible()
    assert row.get_by_role("link", name="Vote").is_visible()
    assert row.get_by_role("link", name="Results").is_visible()


def test_list_shows_newest_poll_first(page, two_polls_newest_first):
    # page: pytest-playwright browser page.
    # two_polls_newest_first: (meetup, lunch) — meetup has the later createdAt.
    newer, older = two_polls_newest_first
    page.goto("/")

    questions = page.locator(".poll-question")
    questions.first.wait_for()
    assert questions.count() == 2
    assert questions.nth(0).inner_text() == newer.question
    assert questions.nth(1).inner_text() == older.question


def test_vote_link_opens_vote_page(page, lunch_spot_poll):
    page.goto("/")
    row = page.locator(".poll-row").filter(has_text=lunch_spot_poll.question)
    row.get_by_role("link", name="Vote").click()

    page.wait_for_url(f"**/vote?id={lunch_spot_poll.poll_id}")
    page.get_by_role("heading", name=lunch_spot_poll.question).wait_for()


def test_results_link_opens_results_page(page, lunch_spot_poll):
    page.goto("/")
    row = page.locator(".poll-row").filter(has_text=lunch_spot_poll.question)
    row.get_by_role("link", name="Results").click()

    page.wait_for_url(f"**/results?id={lunch_spot_poll.poll_id}")
    page.get_by_role("heading", name=lunch_spot_poll.question).wait_for()
