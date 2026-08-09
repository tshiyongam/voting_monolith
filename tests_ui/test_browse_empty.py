"""Browse polls when the table exists but has no items yet."""


def test_empty_list_shows_create_poll_and_no_rows(page, poll_storage):
    # page comes from pytest-playwright; base_url is prepended to "/".
    # poll_storage clears the table before this runs.
    page.goto("/")

    # get_by_role finds elements the way assistive tech does (here: a link
    # whose accessible name is "Create poll"). Prefer this over CSS when you can.
    page.get_by_role("link", name="Create poll").wait_for()
    assert page.locator(".poll-row").count() == 0
