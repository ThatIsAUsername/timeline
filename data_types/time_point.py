from typing import Union
from time import struct_time
from datetime import timedelta
import calendar

UNUSED_STRUCT_FIELDS = (0, 0, 0, 0, 0, -1)  # hour, min, sec, wday, yday, isdst


class TimePoint:

    def __init__(self, year: int = 0, month: int = 0, day: int = 0):
        self._time: struct_time = struct_time((year, month, day) + UNUSED_STRUCT_FIELDS)
        self.DAY_ZERO = None  # Initialized at the bottom of this file.

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

    def __add__(self, delta: timedelta) -> 'TimePoint':
        """
        Create a new TimePoint by adding the timedelta to the time from self.

        Args:
            delta: The time adjustment to use.

        Returns: A new TimePoint resulting from shifting self by delta.
        """
        year = self.year
        month = self.month
        day = self.day + delta.days  # Calculate our new day.

        # If this new day isn't in range, roll the month/year to adjust until it is.
        weekday, month_len = calendar.monthrange(year, month)
        while day < 1 or day > month_len:
            if day < 1:  # We are shifting to the past.

                # Roll the month (and the year if needed).
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1

                # Adjust the day count based on the month we just rolled.
                weekday, month_len = calendar.monthrange(year, month)
                day += month_len

            if day > month_len:  # We are shifting to the future.

                # Roll the month
                month += 1
                if month > 12:
                    month = 1
                    year += 1

                # Adjust the day based on the month we rolled.
                weekday, month_len = calendar.monthrange(year, month)
                day -= month_len

        return TimePoint(year=year, month=month, day=day)

    def __sub__(self, other: Union['TimePoint', timedelta]) -> Union['TimePoint', timedelta]:
        """
        If other is a TimePoint:
            Calculate the timedelta between this date and the other one. Can be negative.
        If other is a timedelta:
            Calculate a new TimePoint gained from subtracting the timedelta from this TimePoint.

        Args:
            other: A TimePoint to differ against or a timedelta to subtract.

        Returns:
            A timedelta with the number of days between the two TimePoints (if other is a TimePoint) or
            the TimePoint calculated by subtracting the timedelta from self.
        """
        # If we are subtracting a timedelta instead of a TimePoint, just invert and pass it to __add__
        if isinstance(other, timedelta):
            return self + timedelta(days=-other.days)

        # If both dates are in the same month, treat this as a special case.
        if self.year == other.year and self.month == other.month:
            return timedelta(days=self.day - other.day)

        # Figure out which date is older, so we can iterate forward thence.
        older, newer = (self, other) if self < other else (other, self)

        total_days = 0
        track_year = older.year
        track_month = older.month

        # Find the number of days left in that month
        weekday, month_len = calendar.monthrange(older.year, older.month)
        total_days += month_len - older.day
        track_month += 1
        # If track_month is too high, roll the year.
        if track_month == 13:
            track_month = 1
            track_year += 1

        # Count days of all months in between.
        while track_year < newer.year or track_month < newer.month:
            # Add the days from track_month, then increment.
            weekday, month_len = calendar.monthrange(track_year, track_month)
            total_days += month_len
            track_month += 1

            # If track_month is too high, roll the year.
            if track_month == 13:
                track_month = 1
                track_year += 1

        # Count days in final month
        total_days += newer.day

        # Negate if self is older than other.
        if self < other:
            total_days = -total_days

        # Convert to a timedelta and return.
        return timedelta(days=total_days)

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
