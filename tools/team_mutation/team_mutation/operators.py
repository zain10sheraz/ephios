"""
Custom mutation operators based on the Ephios signup business rules (see docs/team/REQUIREMENTS.md).

RaiseToReturn      - error signalling: `raise X(...)` -> `return X(...)`. This is exactly the
                     defect class of DEFECT-001 (check_event_is_active returns instead of raises).
StateConstantSwap  - BR3 state rules: replaces a participation state constant with another one.
RuleBoundaryShift  - BR1/BR4/age limit: shifts `>`<->`>=` and `<`<->`<=` but ONLY in comparisons that
                     involve the signup window, capacity or age (identified by name).
"""

import parso.python.tree
from cosmic_ray.operators.operator import Example, Operator

STATES = ["REQUESTED", "CONFIRMED", "USER_DECLINED", "RESPONSIBLE_REJECTED", "GETTING_DISPATCHED"]
BOUNDARY_HINTS = ("timezone.now", "signup_until", "end_time", "maximum_number_of_participants",
                  "minimum_age", "current_count", "age")


class RaiseToReturn(Operator):
    """Replace a `raise` statement with a `return` of the same expression."""

    def mutation_positions(self, node):
        if node.type == "raise_stmt" and len(node.children) == 2:
            yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        keyword = node.children[0]
        assert keyword.value == "raise"
        keyword.value = "return"
        return node

    @classmethod
    def examples(cls):
        return (Example("def f():\n    raise ValueError('x')", "def f():\n    return ValueError('x')"),)


class StateConstantSwap(Operator):
    """Replace a participation state name (e.g. CONFIRMED) with each other state."""

    @staticmethod
    def _alternatives(value):
        return [s for s in STATES if s != value]

    def mutation_positions(self, node):
        if isinstance(node, parso.python.tree.Name) and node.value in STATES:
            for _ in self._alternatives(node.value):
                yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        node.value = self._alternatives(node.value)[index]
        return node

    @classmethod
    def examples(cls):
        return (
            Example("S.CONFIRMED", "S.REQUESTED"),
            Example("S.CONFIRMED", "S.USER_DECLINED", occurrence=1),
        )


_SHIFT = {">": ">=", ">=": ">", "<": "<=", "<=": "<"}


class RuleBoundaryShift(Operator):
    """Shift a comparison boundary, only for comparisons relevant to the business limits."""

    @staticmethod
    def _relevant(node):
        code = node.get_code()
        return any(hint in code for hint in BOUNDARY_HINTS)

    def _points(self, node):
        for i, child in enumerate(node.children[1::2]):
            if child.get_code().strip() in _SHIFT:
                yield i, child

    def mutation_positions(self, node):
        if node.type == "comparison" and self._relevant(node):
            for _, op in self._points(node):
                yield (op.start_pos, op.end_pos)

    def mutate(self, node, index):
        points = list(self._points(node))
        op_idx, op = points[index]
        node.children[op_idx * 2 + 1] = parso.parse(" " + _SHIFT[op.get_code().strip()])
        return node

    @classmethod
    def examples(cls):
        return (
            Example("x = age > minimum_age", "x = age >= minimum_age"),
            Example("x = age < minimum_age", "x = age <= minimum_age"),
        )


def operators():
    return (RaiseToReturn, StateConstantSwap, RuleBoundaryShift)
