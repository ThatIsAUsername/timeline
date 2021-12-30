from typing import List, Tuple, Union
from datetime import date
from calendar import monthrange
from data_types import months


class TimeReference:
    """
    Represents a point in time that may have some uncertainty.
    """

    def __init__(self, absolute: str = '', older: Union[str, List[str]] = '', later: Union[str, List[str]] = ''):
        """

        Args:
            absolute: Either the ID of another event or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event.
                            If so modified, then this event will start and end at the indicated time.
                            If not modified, the beginning and end of this event will match those of the other event.
                        If a date string, the day and month are optional, but day is required if month is present.
                        NOTE: If `absolute` is provided, then `before` and `after` are ignored.
            older: Either another event's ID or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event.
                        If a date string, the day and month are optional, but day is required if month is present.
                        NOTE: This can also be a List of entries to denote multiple constraints.
            later: Either another event's ID or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event.
                        If a date string, the day and month are optional, but day is required if month is present.
                        NOTE: This can also be a List of entries to denote multiple constraints.
        """
        self.min = None
        self.max = None
        self._older_refs = []
        self._later_refs = []

        if absolute:
            tokens = absolute.split()
            if len(tokens) == 1 and not tokens[0].isdigit():
                # This must be a reference to another event.
                tok = tokens[0]
                if tok[0] == '^' or tok[-1] == '$':
                    # If the ref ID is justified, just keep as is and add to both lists.
                    self._older_refs.append(tok)
                    self._later_refs.append(tok)
                else:
                    # If it is not justified, justify it into the relative event lists.
                    self._older_refs.append(f"^{tokens[0]}")
                    self._later_refs.append(f"{tokens[0]}$")
            else:
                # Assume this represents a date string.
                self.min, self.max = self._parse_input(tokens)
        else:
            # Make sure any prior/later events are held in local lists.
            if older:
                temp_refs = older if type(older) is list else [older]
                for tr in temp_refs:
                    # Try to resolve each time to a fixed date. If it's a reference, just store it for later.
                    tokens = tr.split()
                    if len(tokens) == 1 and not tokens[0].isdigit():  # Check if this is a time ref id.
                        self._older_refs.append(tokens[0])
                    else:
                        old_min, old_max = self._parse_input(tokens)
                        self._older_refs.append(old_max if old_max is not None else tr)
            if later:
                temp_refs = later if type(later) is list else [later]
                for tr in temp_refs:
                    # Try to resolve each time to a fixed date. If it's a reference, just store it for later.
                    tokens = tr.split()
                    if len(tokens) == 1 and not tokens[0].isdigit():
                        self._later_refs.append(tokens[0])
                    else:
                        l8r_min, l8r_max = self._parse_input(tr.split())
                        self._later_refs.append(l8r_min if l8r_min is not None else tr)

    @staticmethod
    def _parse_input(tokens: List[str]) -> Tuple[date, date]:

        # if three tokens, expect day month year
        # if two tokens, expect month year; day is min of 1 and max of monthrange(year, month).
        # if one, expect year or record ID. day and month are both min/maxed.
        if len(tokens) == 3:  # Expect DD MMM YYYY (e.g. 21 Jan 2018)
            day_min, month_min, year_min = tokens
            day_min = int(day_min)
            month_min = months.index(month_min.lower())
            year_min = int(year_min)
            day_max, month_max, year_max = day_min, month_min, year_min
        elif len(tokens) == 2:  # Expect MMM YYYY
            month_min, year_min = tokens
            year_min = int(year_min)
            month_min = months.index(month_min.lower())
            year_max, month_max = year_min, month_min
            day_min = 1
            # monthrange returns a tuple of the weekday the month started, and the length of the month.
            weekday, day_max = monthrange(year_max, month_max)
        elif len(tokens) == 1:  # Expect YYYY or a record ID string.
            if tokens[0].isdigit():
                year_min = int(tokens[0])
                year_max = year_min
                month_min = 1
                month_max = 12
                day_min = 1
                # monthrange returns a tuple of the weekday the month started, and the length of the month.
                weekday, day_max = monthrange(year_max, month_max)
            else:
                print(f"Failed to parse input date '{tokens}'")
                return None, None
        elif len(tokens) == 0:
            return None, None

        date_min = date(year=year_min, month=month_min, day=day_min)
        date_max = date(year=year_max, month=month_max, day=day_max)
        return date_min, date_max
