"""Cosmic Ray operator provider exposing the team's business-rule operators as `team/<Name>`."""

from .operators import operators

_OPERATORS = {op.__name__: op for op in operators()}


class TeamProvider:
    def __iter__(self):
        return iter(_OPERATORS)

    def __getitem__(self, name):
        return _OPERATORS[name]
