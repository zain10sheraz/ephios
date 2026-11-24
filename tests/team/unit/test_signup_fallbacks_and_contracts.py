"""Fallback flow/structure for uninstalled plugins and the abstract structure contract."""

import logging
from unittest.mock import patch

import pytest
from django.test import RequestFactory

from ephios.core.signup.fallback import (
    FallbackShiftStructure,
    FallbackSignupFlow,
    default_on_exception,
)
from ephios.core.signup.participants import get_nonlocal_participant_from_request
from ephios.core.signup.structure.abstract import AbstractShiftStructure
from ephios.core.signup.structure.base import BaseShiftStructure
from ephios.plugins.basesignupflows.flow.manual import ManualSignupFlow


@pytest.fixture
def shift(event):
    return event.shifts.get()


def test_missing_flow_disables_signup_with_a_visible_configuration_error(shift, volunteer, caplog):
    shift.signup_flow_slug = "uninstalled-flow"
    shift.save()
    shift.refresh_from_db()
    assert isinstance(shift.signup_flow, FallbackSignupFlow)
    validator = shift.signup_flow.get_validator(volunteer.as_participant())
    assert validator.can_sign_up() is False
    assert "Signup configuration is invalid!" in " ".join(
        str(e) for e in validator.get_action_errors()
    )
    with pytest.raises(TypeError):
        shift.signup_flow._configure_participation(None)
    caplog.clear()  # the fallback logs a warning about the missing flow on purpose


def test_missing_structure_uses_the_fallback_structure(shift, caplog):
    shift.structure_slug = "uninstalled-structure"
    shift.save()
    shift.refresh_from_db()
    assert isinstance(shift.structure, FallbackShiftStructure)
    caplog.clear()


def test_manual_flow_cannot_configure_a_participation(shift):
    flow = ManualSignupFlow(shift)
    with pytest.raises(TypeError):
        flow._configure_participation(None)


def test_default_on_exception_returns_default_and_logs():
    records = []

    class Collect(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = Collect(level=logging.ERROR)
    ephios_logger = logging.getLogger("ephios")  # does not propagate, so caplog cannot see it
    ephios_logger.addHandler(handler)
    try:

        @default_on_exception(default=lambda: "fallback value")
        def explode():
            raise RuntimeError("boom")

        @default_on_exception(default=5)
        def explode_with_constant():
            raise RuntimeError("boom")

        @default_on_exception()
        def works():
            return "fine"

        assert explode() == "fallback value"
        assert explode_with_constant() == 5
        assert works() == "fine"
    finally:
        ephios_logger.removeHandler(handler)
    assert len(records) == 2
    assert all("errored" in message for message in records)


@pytest.mark.parametrize(
    "name", ["slug", "verbose_name", "description", "disposition_participation_form_class"]
)
def test_abstract_structure_properties_must_be_overridden(name):
    getter = getattr(AbstractShiftStructure, name).fget
    with pytest.raises(NotImplementedError):
        getter(None)


@pytest.mark.parametrize(
    "name, args",
    [
        ("get_configuration_form", ()),
        ("get_checkers", ()),
        ("render", (None,)),
        ("get_signup_info", ()),
        ("get_list_export_data", ()),
        ("get_participant_count_bounds", ()),
        ("get_signup_stats", ()),
    ],
)
def test_abstract_structure_methods_must_be_overridden(name, args):
    method = getattr(AbstractShiftStructure, name)
    with pytest.raises(NotImplementedError):
        method(None, *args)


def test_abstract_structure_optional_hooks_and_defaults():
    assert AbstractShiftStructure.get_signup_form_fields(None, None, None, None) is None
    assert AbstractShiftStructure.save_signup(None, None, None, None, None) is None
    assert AbstractShiftStructure.has_customized_signup(None, None) is False


def test_base_structure_defaults(shift):
    structure = FallbackShiftStructure(shift)
    assert structure.get_signup_form_fields(None, None, None) == {}
    assert structure.get_participant_count_bounds() == (None, None)
    with pytest.raises(NotImplementedError):
        _ = BaseShiftStructure.shift_state_template_name.fget(structure)
    export = structure.get_list_export_data()
    assert export == []


def test_nonlocal_participant_comes_from_the_first_receiver_that_answers(volunteer):
    sentinel = volunteer.as_participant()
    with patch(
        "ephios.core.signup.participants.participant_from_request.send",
        return_value=[(None, None), (None, sentinel)],
    ):
        assert get_nonlocal_participant_from_request(RequestFactory().get("/")) is sentinel


def test_logging_import_is_available():
    assert logging.getLogger("ephios") is not None


def test_structure_render_falls_back_to_error_fragment_and_logs(shift):
    from django.template import Context

    structure = shift.structure
    context = Context({})
    context.request = RequestFactory().get("/")
    records = []

    class Collect(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = Collect(level=logging.ERROR)
    ephios_logger = logging.getLogger("ephios")
    ephios_logger.addHandler(handler)
    try:
        with patch.object(
            type(structure), "get_shift_state_context_data", side_effect=RuntimeError("bad data")
        ):
            html = structure.render(context)
    finally:
        ephios_logger.removeHandler(handler)
    assert len(records) == 1
    assert "state render failed" in records[0]
    assert html  # the error fragment was rendered instead of crashing the page


def test_structure_configuration_form_without_a_shift(event):
    from ephios.plugins.baseshiftstructures.structure.uniform import UniformShiftStructure

    form = UniformShiftStructure(None, event=event).get_configuration_form(
        request=RequestFactory().get("/")
    )
    assert "maximum_number_of_participants" in form.fields


def test_configuration_form_context_exposes_request_event_and_shift(shift):
    request = RequestFactory().get("/")
    form = shift.signup_flow.get_configuration_form(request=request)
    context = form.get_context()
    assert context["request"] is request
    assert context["event"] == shift.event
    assert context["shift"] == shift
