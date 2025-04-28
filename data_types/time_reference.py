from typing import List, Tuple, Union
from calendar import monthrange, month_abbr
from data_types import TimePoint

months = list(month_abbr)


def is_year(token: str) -> bool:
    if isinstance(token, List):
        if len(token) == 1:
            token = token[0]
        else:
            return False

    # If this token starts with [0-9-+], then it's probably a year.
    return (
        token[0].isdigit()
        or len(token) > 1 and (token[0] == '-' or token[0] == '+')
        )


def is_offset(tokens: List[str]) -> bool:
    # If we are doing math ('+' or '-' appear as tokens) then it's probably an offset, not a date string.
    # Note that offsets are relative to event references, so if is_offset returns true, so should is_event_ref.
    return ('+' in tokens or '-' in tokens) and (tokens[0][0].isalpha() or tokens[0][0] == '^')


def is_event_ref(tokens: List[str]) -> bool:
    # If it's an offset (a +/- calculation), then it's referencing another event.
    # If not a calculation, it may be a date or an event reference.
    return is_offset(tokens) or len(tokens) == 1 and not is_year(tokens[0])


class TimeReference:
    """
    Represents a point in time that may have some uncertainty.
    """

    def __init__(self, absolutes: List[str] = None, older: List[str] = None, later: List[str] = None):
        """

        Args:
            absolutes: Either the ID of another event or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event.
                            If so modified, then this event will start and end at the indicated time.
                            If not modified, the beginning and end of this event will match those of the other event.
                        If a date string, the day and month are optional, but month is required if day is present.
                        NOTE: This can also be a List of entries to denote multiple constraints.
            older: Either another event's ID or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event, and
                        may also specify a math-based offset, e.g. "otherevent + 1y 2m 3d'
                        If a date string, the day and month are optional, but day is required if month is present.
                        NOTE: This can also be a List of entries to denote multiple constraints.
            later: Either another event's ID or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event, and
                        may also specify a math-based offset, e.g. "otherevent - 1y 2m 3d'
                        If a date string, the day and month are optional, but day is required if month is present.
                        NOTE: This can also be a List of entries to denote multiple constraints.
        """
        self.min: TimePoint = None
        self.max: TimePoint = None

        self._older_refs, self._later_refs = self._unpack_constraints(absolutes, older, later)

    def __str__(self) -> str:
        return f"{self.min}-{self.max}"

    def _unpack_constraints(self, absolutes: List[str] = None, older: List[str] = None, later: List[str] = None) -> Tuple[List, List]:
        aoc, alc = self._unpack_absolute_constraints(absolutes)
        roc, rlc = self._unpack_relative_constraints(older, later)
        older_constraints = aoc + roc
        later_constraints = alc + rlc

        return older_constraints, later_constraints

    def _unpack_absolute_constraints(self, absolutes: List[str] = None) -> Tuple[List, List]:
        older_constraints = []
        later_constraints = []
        absolutes = absolutes or []
        for absolute in absolutes:
            tokens = absolute.split()

            if is_event_ref(tokens):
                tok = tokens[0]
                offset_text = f"{absolute[len(tok):]}"  # Extract offset text if present.

                justified = tok[0] == '^' or tok[-1] == '$'
                if offset_text and not justified:
                    # If we have an offset, then we assume a justification to the nearest boundary unless specified.
                    # e.g. if we have a negative offset from another event, justify to the event's start.min.
                    tok = f"^{tok}" if '-' in offset_text else f"{tok}$"

                if tok[0] == '^' or tok[-1] == '$':
                    # If the ref ID is justified, just keep as is and add to both lists.
                    older_constraints.append(f"{tok}{offset_text}")
                    later_constraints.append(f"{tok}{offset_text}")
                else:
                    # If it is not justified, justify it into the relative event lists.
                    older_constraints.append(f"^{tokens[0]}{offset_text}")
                    later_constraints.append(f"{tokens[0]}${offset_text}")
            else:
                # Assume this represents a date string.
                amin, amax = self._parse_input(tokens)
                if amin:
                    older_constraints = [amin]
                if amax:
                    later_constraints = [amax]

        return older_constraints, later_constraints

    def _unpack_relative_constraints(self, older: List[str] = None, later: List[str] = None) -> Tuple[List, List]:
        older_constraints = []
        later_constraints = []
        # Make sure any prior/later events are held in local lists.
        if older:
            temp_refs = older if type(older) is list else [older]
            for tr in temp_refs:
                # Try to resolve each time to a fixed date. If it's a reference, just store it for later.
                tokens = tr.split()
                if is_event_ref(tokens):
                    older_constraints.append(tr)
                else:
                    old_min, old_max = self._parse_input(tokens)
                    oc = old_max if old_max is not None else tr
                    older_constraints.append(oc)
        if later:
            temp_refs = later if type(later) is list else [later]
            for tr in temp_refs:
                # Try to resolve each time to a fixed date. If it's a reference, just store it for later.
                tokens = tr.split()
                if is_event_ref(tokens):
                    later_constraints.append(tr)
                else:
                    l8r_min, l8r_max = self._parse_input(tr.split())
                    later_constraints.append(l8r_min if l8r_min is not None else tr)

        return older_constraints, later_constraints

    @staticmethod
    def _parse_input(tokens: List[str]) -> Tuple[TimePoint, TimePoint]:

        # if three tokens, expect day month year
        # if two tokens, expect month year; day is min of 1 and max of monthrange(year, month).
        # if one, expect year or record ID. day and month are both min/maxed.
        if len(tokens) == 3:  # Expect DD MMM YYYY (e.g. 21 Jan 2018)
            day_min, month_min, year_min = tokens
            day_min = int(day_min)
            month_min = months.index(month_min[:3].title())
            year_min = int(year_min)
            day_max, month_max, year_max = day_min, month_min, year_min
        elif len(tokens) == 2:  # Expect MMM YYYY
            month_min, year_min = tokens
            year_min = int(year_min)
            month_min = months.index(month_min[:3].title())
            year_max, month_max = year_min, month_min
            day_min = 1
            # monthrange returns a tuple of the weekday the month started, and the length of the month.
            weekday, day_max = monthrange(year_max, month_max)
        elif len(tokens) == 1:  # Expect YYYY or a record ID string.
            token = tokens[0]
            c0 = token[0]
            if c0.isdigit() or c0 == '-' or c0 == '+':
                year_min = int(token)
                year_max = year_min
                month_min = 1
                month_max = 12
                day_min = 1
                # monthrange returns a tuple of the weekday the month started, and the length of the month.
                weekday, day_max = monthrange(year_max, month_max)
            else:
                raise ValueError(f"Failed to parse input date '{tokens}'")
        elif len(tokens) == 0:
            return None, None
        else:
            raise ValueError(f"Could not parse input date '{tokens}'")

        date_min = TimePoint(year=year_min, month=month_min, day=day_min)
        date_max = TimePoint(year=year_max, month=month_max, day=day_max)
        return date_min, date_max

    def has_min(self) -> bool:
        return type(self.min) is TimePoint

    def has_max(self) -> bool:
        return type(self.max) is TimePoint
