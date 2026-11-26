"""Usability tests (one per workflow) and a keyboard test, all in the real browser.

WF1 test: first submit a value the rule rejects, check that the error explains what to correct, correct it, check success.
WF2 test: complete the task and check the confirmation shown.
Keyboard test (WF1 form): focus reaches the required fields and the submit button in the expected order and the keyboard can submit.
"""

from tests.team.e2e.pages import (
    alerts,
    create_event_in_ui,
    event_path,
    field_errors,
    fill_shift_form,
    save_shift,
    sign_up_button,
)

REQUIRED_IN_ORDER = ["id_date", "id_meeting_time", "id_start_time", "id_end_time"]


def test_usability_wf1_error_explains_what_to_correct_then_success(planner_page, server):
    create_event_in_ui(planner_page, server.base, "Usability WF1")
    fill_shift_form(planner_page, meeting_time="11:00", start_time="10:00")
    save_shift(planner_page)
    errors = field_errors(planner_page)
    assert errors == [
        "Meeting time must not be after start time!"
    ]  # names the field and says what is wrong
    assert planner_page.input_value("#id_meeting_time") == "11:00"  # the entered values are kept
    planner_page.fill("#id_meeting_time", "09:00")  # correct the value
    save_shift(planner_page)
    assert any("Usability WF1 has been saved" in text for text in alerts(planner_page))


def test_usability_wf2_volunteer_signs_up_and_sees_a_confirmation(
    volunteer_page, planner_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    volunteer_page.goto(server.base + event_path(planner_api, event_id))
    sign_up_button(volunteer_page, shift_id).click()
    volunteer_page.wait_for_load_state()
    assert any("successfully signed up" in text for text in alerts(volunteer_page))


def focus_trail(page, stop_text):
    """Press Tab from the first field and record the id (or text) of every newly focused element until the stop text."""
    trail = []
    for _ in range(60):
        page.keyboard.press("Tab")
        label = page.evaluate(
            "document.activeElement.id || document.activeElement.innerText.trim()"
        )
        if label and (not trail or trail[-1] != label):
            trail.append(label)
        if stop_text in label:
            break
    return trail


def test_keyboard_navigation_reaches_required_fields_and_submits(planner_page, server):
    create_event_in_ui(planner_page, server.base, "Keyboard WF1")
    fill_shift_form(planner_page)
    planner_page.focus("#id_date")
    trail = ["id_date"] + focus_trail(planner_page, "Save event")
    positions = [trail.index(field) for field in REQUIRED_IN_ORDER]
    assert positions == sorted(positions)  # required fields are reached in document order
    assert "Save event" in trail[-1]  # the submit button is reached by keyboard
    with planner_page.expect_navigation():
        planner_page.keyboard.press(
            "Enter"
        )  # the keyboard submits the form from the focused Save button
    assert any("Keyboard WF1 has been saved" in text for text in alerts(planner_page))
