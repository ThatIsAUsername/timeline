
from typing import List, Union

from datetime import date, timedelta
from data_types import Timeline, TimeReference, EventRecord


class Timeview:

    # Determines how much to adjust the view when zooming.
    # Values must be [0-1], where lower numbers cause more change.
    ZOOM_RATIO = 0.8

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

    def zoom_in(self, focus: date) -> None:
        """
        Changes the view's min and/or max to narrow the view on the provided date.
        Args:
            focus: The date to zoom in towards.

        Returns:
            None
        """
        assert self.contains(focus), "Cannot zoom on a date outside the view"

        min_ord = self.min.toordinal()
        max_ord = self.max.toordinal()
        foc_ord = focus.toordinal()

        lo_shift = timedelta((foc_ord - min_ord) * (1-self.ZOOM_RATIO))
        hi_shift = timedelta((max_ord - foc_ord) * (1-self.ZOOM_RATIO))

        self.min = self.min + lo_shift
        self.max = self.max - hi_shift

    def zoom_out(self, focus: date) -> None:
        """
        Changes the view's min and/or max to widen the view around the provided date.
        Args:
            focus: The date to zoom out from.

        Returns:
            None
        """
        assert self.contains(focus), "Cannot zoom on a date outside the view"

        min_ord = self.min.toordinal()
        max_ord = self.max.toordinal()
        foc_ord = focus.toordinal()

        zoom_frac = 1/(1-self.ZOOM_RATIO)
        lo_shift = timedelta((foc_ord - min_ord) * (1-self.ZOOM_RATIO))
        hi_shift = timedelta((max_ord - foc_ord) * (1-self.ZOOM_RATIO))

        self.min = self.min - hi_shift
        self.max = self.max + lo_shift
