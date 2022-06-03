
from dataclasses import dataclass


@dataclass
class TimeSpan:

    years: int = 0
    months: int = 0
    days: int = 0

    def invert(self):
        self.years = -self.years
        self.months = -self.months
        self.days = -self.days

    @staticmethod
    def parse(input_str: str) -> 'TimeSpan':
        """
        Parse an EventDuration from a string.
        The string may be formatted with up to three whitespace-separated tokens to
        indicate years, months, and days. E.g. '1y 2m 3d'. One or all may be specified.

        Args:
            input_str: A string formatted as [#y] [#m] [#d] to indicate the years, months, and days of duration.

        Returns:
            A new EventDuration object.
        """
        tokens = input_str.split()
        years = 0
        months = 0
        days = 0
        for tok in tokens:
            if tok[-1] == 'y':
                years = int(tok[:-1])
            elif tok[-1] == 'm':
                months = int(tok[:-1])
            elif tok[-1] == 'd':
                days = int(tok[:-1])
            else:
                raise ValueError(f"Token {tok} doesn't specify a unit (must be d, m, or y)!")

        return TimeSpan(years=years, months=months, days=days)

    def __eq__(self, other: 'TimeSpan'):
        return self.years == other.years and self.months == other.months and self.days == other.days
