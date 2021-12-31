
from datetime import date, timedelta

from data_types import Timeline


class Timeview:

    def __init__(self, timeline: Timeline):
        self.timeline = timeline
        self.min = self.timeline.min
        self.max = self.timeline.max

    def contains(self, d: date) -> bool:
        return self.min <= d <= self.max
