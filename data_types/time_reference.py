from typing import List, Tuple, Union
from datetime import date
from calendar import monthrange
from data_types import months


class TimeReference:
    """
    Represents a point in time that may have some uncertainty.
    """

    def __init__(self, absolute: str = '', before: Union[str, List[str]] = '', after: Union[str, List[str]] = ''):
        """

        Args:
            absolute: Either the ID of another event or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event.
                        If a date string, the day and month are optional, but day is required if month is present.
            before: Either another event's ID or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event.
                        If a date string, the day and month are optional, but day is required if month is present.
                        NOTE: This can also be a List of entries to denote multiple constraints.
            after: Either another event's ID or a string representation of a date, formatted as 'DD MMM YYYY'
                        If an ID, it may be modified to denote the start (^id) or end (id$) of the other event.
                        If a date string, the day and month are optional, but day is required if month is present.
                        NOTE: This can also be a List of entries to denote multiple constraints.
        """
        abs_min, abs_max = self._parse_input(absolute) if absolute else (None, None)
        bef_min, bef_max = self._parse_input(before) if before else (None, None)
        aft_min, aft_max = self._parse_input(after) if after else (None, None)

        min_list = [mm for mm in [abs_min, bef_min, aft_min] if mm is not None]
        max_list = [mm for mm in [abs_max, bef_max, aft_max] if mm is not None]
        self.min = min(min_list, key=lambda x: x.toordinal())
        self.max = min(max_list, key=lambda x: x.toordinal())
        # self.max = None
        # self.afters = []
        # self.befores = []

    @staticmethod
    def _parse_input(input_str: str) -> Tuple[date, date]:

        # if three tokens, expect day month year
        # if two tokens, expect month year; day is min of 1 and max of monthrange(year, month).
        # if one, expect year or record ID. day and month are both min/maxed.
        tokens = input_str.split()
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
            day_max = monthrange(year_max, month_max)
        elif len(tokens) == 1:  # Expect YYYY or a record ID string.
            if tokens[0].isdigit():
                year_min = int(tokens[0])
                year_max = year_min
                month_min = 1
                month_max = 12
                day_min = 1
                day_max = monthrange(year_max, month_max)
            else:
                print("TODO: Handle record references")
                # id_ref = tokens[0]
                # if id_ref[0] == '^':
                #     date_max = id_ref[1:]

                # day_min, month_min, year_min = tokens*3
                # day_max, month_max, year_max = day_min, month_min, year_min
                return None, None
        elif len(tokens) == 0:
            return None, None

        date_min = date(year=year_min, month=month_min, day=day_min)
        date_max = date(year=year_max, month=month_max, day=day_max)
        return date_min, date_max
