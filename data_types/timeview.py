
from typing import List, Union

from datetime import date
from data_types import Timeline, TimeReference, EventRecord


class Timeview:

    def __init__(self, timeline: Timeline):
        self.timeline = timeline
        self.min: date = self.timeline.min
        self.max: date = self.timeline.max

    def contains(self, timelike: Union[date, TimeReference, EventRecord]) -> bool:
        if type(timelike) is date:
            return self.contains_date(timelike)
        elif type(timelike) is TimeReference:
            return self.contains_reference(timelike)
        elif type(timelike) is EventRecord:
            return self.contains_record(timelike)

    def contains_date(self, d: date) -> bool:
        """
        Determine whether the date `d` is currently visible to the Timeview.
        Args:
            d: A date to compare

        Returns:
            True if `d` falls within the Timeview's purview, false otherwise.
        """
        return self.min <= d <= self.max

    def contains_reference(self, tr: TimeReference) -> bool:
        """
        Determine whether the given time reference is visible to the Timeview
        Args:
            tr: A normalized TimeReference (min and max must not be None).

        Returns:
            True if the TimeReference should be visible in this Timeview, false otherwise.
        """
        if type(tr.max) is date and tr.max < self.min \
                or type(tr.min) is date and tr.min > self.max:
            return False

        return True

    def contains_record(self, rec: EventRecord) -> bool:
        """
        Determine whether the provided EventRecord is visible to this Timeview.
        Args:
            rec: A normalized EventRecord

        Returns:
            True if the EventRecord would be at least partly visible within this Timeview, else False.
        """
        return self.contains_reference(rec.start) or self.contains_reference(rec.end)

    def get_visible(self) -> List[EventRecord]:
        """
        Returns:
            A list of all records from this view's Timeline that are also currently within the view.
        """
        visible_records = []
        for rec in self.timeline.get_records().values():
            if self.contains(rec):
                visible_records.append(rec)
        return visible_records
