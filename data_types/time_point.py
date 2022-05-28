
from typing import Union
from time import struct_time
from datetime import date, timedelta
from data_types import TimeSpan
import calendar
import math

UNUSED_STRUCT_FIELDS = (0, 0, 0, 0, 0, -1)  # hour, min, sec, wday, yday, isdst


def construct_time(year, month, day) -> struct_time:
    """
    Utility function to construct a valid struct_time, wrapping day/month fields as needed.
    Args:
        year: The year to represent.
        month: The month in the given year. Will be wrapped (changing the year) if out of bounds.
        day: The day in the given month. Will be wrapped (changing the month/year) if out of bounds.

    Returns:
        A struct_time object representing the described point in time.
    """
    # If the values are trivially valid, just construct and return.
    if (1 <= month <= 12) and (1 <= day <= 28):
        return struct_time((year, month, day) + UNUSED_STRUCT_FIELDS)

    # Otherwise, wrap if needed, starting at the month level.
    while month > 12:
        year += 1
        month -= 12
    while month < 1:
        year -= 1
        month += 12

    # Done. Now wrap days. First find the number of days in the current month.
    weekday, month_len = calendar.monthrange(year, month)

    # Handle the case where days is larger than the current month.
    while day > month_len:
        day -= month_len
        month = month + 1
        if month > 12:  # Wrap to January.
            year += 1
            month = 1
        weekday, month_len = calendar.monthrange(year, month)  # Get the new month length.

    # Handle the case where days is negative.
    while day < 1:
        month -= 1
        if month < 1:
            year -= 1
            month = 12
        weekday, month_len = calendar.monthrange(year, month)  # Get the length of the prior month.
        day += month_len

    # Construct our final reconciled struct_time.
    return struct_time((year, month, day) + UNUSED_STRUCT_FIELDS)


class TimePoint:
    """
    Sure datetime already exists, but it only goes back to year 1. TimePoint is a wrapper around a
    struct_time object to provide an easy interface while supporting a wide date range.
    """
    def __init__(self, year: int = 0, month: int = 0, day: int = 0):
        self._time: struct_time = construct_time(year, month, day)
        self.DAY_ZERO = None  # Initialized at the bottom of this file.

    def __repr__(self) -> str:
        return f"TimePoint(year={self.year}, month={self.month}, day={self.day})"

    @staticmethod
    def from_ordinal(ordinal: int) -> 'TimePoint':
        td = timedelta(days=ordinal)
        tp = TimePoint.DAY_ZERO + td
        return tp

    def ordinal(self) -> int:
        """
        Represent this point in time as an integer for direct comparisons.
        the calendar module sets 1 BC as year zero, so we will follow their lead and say that
        Dec 31 of year 0 is day zero (so Jan 1 of 1 AD is day 1).
        Returns: The number of days from Dec 31 of 1 BC.
        """
        delta: timedelta = self - TimePoint.DAY_ZERO
        return delta.days

    # ------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------

    def set_error(self, value):
        raise AttributeError('Cannot modify TimePoint fields after construction.')

    def del_error(self):
        raise AttributeError('Cannot modify TimePoint fields after construction.')

    def get_year(self):
        return self._time.tm_year

    def get_month(self):
        return self._time.tm_mon

    def get_day(self):
        return self._time.tm_mday

    year = property(get_year, set_error, del_error)
    month = property(get_month, set_error, del_error)
    day = property(get_day, set_error, del_error)

    # ------------------------------------------------------------
    # Operator overrides
    # ------------------------------------------------------------

    def __add__(self, delta: Union[timedelta, TimeSpan]) -> 'TimePoint':
        """
        Create a new TimePoint by adding the timedelta to the time from self.

        Args:
            delta: The time adjustment to use.

        Returns: A new TimePoint resulting from shifting self by delta.
        """
        year = self.year
        month = self.month
        day = self.day

        # Handle the case delta is an EventDuration.
        if isinstance(delta, TimeSpan):
            return TimePoint(year=year+delta.years, month=month+delta.months, day=day+delta.days)
        elif isinstance(delta, timedelta):
            # timedelta is specified only in days.
            return TimePoint(year=year, month=month, day=day+delta.days)
        else:
            raise ValueError(f"Cannot add a {type(delta)} to a TimePoint!")

    def __sub__(self, other: Union['TimePoint', timedelta, TimeSpan]) -> Union['TimePoint', timedelta]:
        """
        If other is a TimePoint:
            Calculate the timedelta between this date and the other one. Can be negative.
        If other is a timedelta:
            Calculate a new TimePoint gained from subtracting the timedelta from this TimePoint.

        Args:
            other: A TimePoint to differ against or a timedelta to subtract.

        Returns:
            If other is a TimePoint: A timedelta with the number of days between the two TimePoints, or
            If other is a timedelta: The TimePoint calculated by subtracting the timedelta from self.
        """
        # If we are subtracting a timedelta instead of a TimePoint, just invert and pass it to __add__
        if isinstance(other, timedelta):
            return self + timedelta(days=-other.days)
        if isinstance(other, TimeSpan):
            return TimePoint(year=self.year-other.years, month=self.month-other.months, day=self.day-other.days)

        # If both dates are in the same month, treat this as a special case.
        if self.year == other.year and self.month == other.month:
            return timedelta(days=self.day - other.day)

        self_ok = 1 <= self.year <= 9999
        other_ok = 1 <= other.year <= 9999
        if self_ok and other_ok:
            # If we are in the normal range, let datetime do the work.
            try:
                difference: timedelta = date(*self._time[:3]) - date(*other._time[:3])
                return difference
            except (ValueError, OverflowError) as err:
                # ValueError if the datetime is constructed out of range,
                # OverflowError if subtracting a timedelta takes it out of range.
                pass  # Fall through to handle this case manually.

        # This calculation occurs outside the accepted range for datetime [1, 9999].
        # Ensure both dates are inside that range and try again.
        # Note this just straightforwardly extends the current calendar back with leap
        # years and everything, so may not match historic dating systems.

        # Get the number of millenia away from the year 2000, so we can shift into the valid range.
        shift_self_years = 0 if self_ok else 1000 * int(float(2000-self.year) / 1000)
        shift_other_years = 0 if other_ok else 1000 * int(float(2000-other.year) / 1000)
        days_per_year = 365.2425
        shift_self_days = math.floor(shift_self_years * days_per_year)
        shift_other_days = math.floor(shift_other_years * days_per_year)

        # Create shifted date objects inside the valid range for datetime.date.
        self_adj = self.year+shift_self_years
        other_adj = other.year+shift_other_years
        self_dt = date(*(self_adj,) + self._time[1:3])
        other_dt = date(*(other_adj,) + other._time[1:3])

        # All right. Finally we can just... subtract.
        diff_days = (self_dt - other_dt).days

        # Not done yet though; have to roll the deltas back in from when we initially shifted each date.
        diff_days = (diff_days + (shift_other_days - shift_self_days))
        delta = timedelta(days=diff_days)
        return delta

    def __gt__(self, other: 'TimePoint'):
        if isinstance(other, TimePoint):
            return self._time > other._time
        return NotImplemented

    def __lt__(self, other: 'TimePoint'):
        if isinstance(other, TimePoint):
            return self._time < other._time
        return NotImplemented

    def __eq__(self, other: 'TimePoint'):
        if isinstance(other, TimePoint):
            return self._time == other._time
        return NotImplemented

    def __le__(self, other: 'TimePoint'):
        if isinstance(other, TimePoint):
            return self._time <= other._time
        return NotImplemented

    def __ge__(self, other: 'TimePoint'):
        if isinstance(other, TimePoint):
            return self._time >= other._time
        return NotImplemented


# Declare a known constant as a baseline.
TimePoint.DAY_ZERO = TimePoint(year=0, month=12, day=31)
