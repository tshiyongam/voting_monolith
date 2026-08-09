"""Open a poll to vote and cast a vote."""


def test_vote_page_shows_question_options_and_total(page, lunch_spot_poll):
    # page: pytest-playwright browser page.
    # lunch_spot_poll: sample with a known total (43) and option labels.
    page.goto(f"/vote?id={lunch_spot_poll.poll_id}")

    page.get_by_role("heading", name=lunch_spot_poll.question).wait_for()
    assert page.get_by_text("43 votes").is_visible()
    for option in lunch_spot_poll.options:
        page.get_by_role("button", name=option["text"]).wait_for()


def test_cast_vote_navigates_to_results(page, meetup_poll):
    page.goto(f"/vote?id={meetup_poll.poll_id}")
    first_choice = meetup_poll.options[0]["text"]
    page.get_by_role("button", name=first_choice).click()

    page.wait_for_url(f"**/results?id={meetup_poll.poll_id}")
    page.get_by_role("heading", name=meetup_poll.question).wait_for()
    assert page.locator("#vote-count").inner_text() == "1 vote"
    # First option should show one vote; others stay at zero.
    first_row = page.locator(".results-list li").filter(has_text=first_choice)
    assert first_row.locator(".result-count").inner_text() == "1"


def test_vote_page_shows_not_found_for_unknown_id(page, poll_storage):
    page.goto("/vote?id=does-not-exist")
    error = page.locator("#page-error")
    error.wait_for()
    assert "not found" in error.inner_text().lower()
