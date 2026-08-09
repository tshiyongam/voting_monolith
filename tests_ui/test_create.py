"""Create a poll (and cancel / validation)."""


def test_create_poll_navigates_to_vote_page(page, poll_storage):
    # page: pytest-playwright browser page.
    # poll_storage: start with no rows so the new poll is easy to reason about.
    page.goto("/create")

    page.locator("#question").fill("Which snack for the study group?")
    page.locator("#option-1").fill("Fruit")
    page.locator("#option-2").fill("Chips")
    page.get_by_role("button", name="Create").click()

    page.wait_for_url("**/vote?id=*")
    page.get_by_role("heading", name="Which snack for the study group?").wait_for()
    page.get_by_role("button", name="Fruit").wait_for()
    page.get_by_role("button", name="Chips").wait_for()
    assert page.get_by_text("0 votes").is_visible()


def test_cancel_returns_to_poll_list(page, poll_storage):
    page.goto("/create")
    page.get_by_role("link", name="Cancel").click()
    page.wait_for_url("**/")
    page.get_by_role("link", name="Create poll").wait_for()


def test_create_shows_error_when_question_missing(page, poll_storage):
    page.goto("/create")
    page.locator("#option-1").fill("Yes")
    page.locator("#option-2").fill("No")
    page.get_by_role("button", name="Create").click()

    error = page.locator("#form-error")
    error.wait_for()
    assert error.inner_text() == "Enter a question."
    assert "/create" in page.url
