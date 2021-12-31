
from datetime import date, timedelta

from data_types import Timeline


class Timeview:

    def __init__(self, timeline: Timeline):
        self.timeline = timeline
        delta: timedelta = timeline.max - timeline.min
        buffer_pct = 0.02
        buffer_sec = delta.total_seconds() * buffer_pct
        buffer_delta = timedelta(seconds=buffer_sec)

        self.min = self.timeline.min - buffer_delta
        self.max = self.timeline.max + buffer_delta
