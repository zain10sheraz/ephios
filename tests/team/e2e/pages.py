"""Small helpers that drive the real Ephios pages (selectors were taken from the rendered pages)."""

import re
from urllib.parse import urlparse

DEFAULT_SHIFT = {
    "date": "2099-03-01",
    "meeting_time": "09:00",
    "start_time": "10:00",
    "end_time": "16:00",
    "maximum": "5",
}


def event_path(api, event_id):
    """Path of the event page (it contains a slug), read from the REST API."""
    return urlparse(api.rest(f"/api/events/{event_id}/")["frontend_url"]).path


def alerts(page):
    return [
        alert.inner_text().strip().replace("\n", " ") for alert in page.query_selector_all(".alert")
    ]


def field_errors(page):
    return [
        error.inner_text().strip()
        for error in page.query_selector_all(".invalid-feedback, .alert-danger")
    ]


def submit_without_browser_validation(page):
    """The browser blocks empty required fields before sending; switch that off to exercise the server-side rule."""
    page.evaluate("document.querySelector('form').setAttribute('novalidate', '')")
    page.click("button[type=submit]")
    page.wait_for_load_state()


def create_event_in_ui(page, base, title, location="Test hall"):
    """Fill and submit the create-event form; return the new event id taken from the redirect to the add-shift page."""
    page.goto(f"{base}/events/create/1/")
    page.fill("#id_title", title)
    page.fill("#id_location", location)
    page.click("button[type=submit]")
    page.wait_for_url(re.compile(r"/events/\d+/createshift/"))
    return int(re.search(r"/events/(\d+)/createshift/", page.url).group(1))


def fill_shift_form(page, flow="instant_confirmation", **overrides):
    values = {**DEFAULT_SHIFT, **overrides}
    page.fill("#id_date", values["date"])
    page.fill("#id_meeting_time", values["meeting_time"])
    page.fill("#id_start_time", values["start_time"])
    page.fill("#id_end_time", values["end_time"])
    page.select_option("#id_signup_flow_slug", flow)
    page.fill("#id_maximum_number_of_participants", values["maximum"])


def save_shift(page):
    page.click("button[type=submit]:has-text('Save')")
    page.wait_for_load_state()


def sign_up_button(page, shift_id, choice="sign_up"):
    return page.locator(f"#shift-{shift_id} button[name=signup_choice][value={choice}]")


def shift_box_text(page, shift_id):
    return page.inner_text(f"#shift-{shift_id}").replace("\n", " | ")


def own_states(api, shift_id):
    """States (0 requested, 1 confirmed, 2 declined) of the logged-in user's participations on a shift, from REST."""
    results = api.rest("/api/users/me/participations/", shift=shift_id, limit=1000)["results"]
    return [participation["state"]["value"] for participation in results]
