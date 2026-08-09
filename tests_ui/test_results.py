"""View results without necessarily casting a vote."""


def test_results_page_shows_counts_and_total(page, lunch_spot_poll):
    # page: pytest-playwright browser page.
    # lunch_spot_poll: sample with a known vote breakdown.
    page.goto(f"/results?id={lunch_spot_poll.poll_id}")

    page.get_by_role("heading", name=lunch_spot_poll.question).wait_for()
    assert page.locator("#vote-count").inner_text() == "43 votes"

    for option in lunch_spot_poll.options:
        row = page.locator(".results-list li").filter(has_text=option["text"])
        row.wait_for()
        assert row.locator(".result-count").inner_text() == str(option["votes"])


def test_results_vote_again_returns_to_vote_page(page, lunch_spot_poll):
    page.goto(f"/results?id={lunch_spot_poll.poll_id}")
    page.get_by_role("button", name="Vote or vote again").click()

    page.wait_for_url(f"**/vote?id={lunch_spot_poll.poll_id}")
    page.get_by_role("heading", name=lunch_spot_poll.question).wait_for()


def test_results_page_shows_not_found_for_unknown_id(page, poll_storage):
    page.goto("/results?id=does-not-exist")
    error = page.locator("#page-error")
    error.wait_for()
    assert "not found" in error.inner_text().lower()
