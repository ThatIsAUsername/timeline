from typing import Dict, List
import yaml
import math

from datetime import date
from data_types import EventRecord, TimePoint, IncoherentTimelineError
import algorithms


class Timeline:
    def __init__(self):
        self.records = {}  # Map record ID to record
        self.min = -math.inf
        self.max = math.inf

    def load_from_file(self, filename: str):
        with open(filename) as file:
            loaded = yaml.load(file, Loader=yaml.BaseLoader)

        self.load_from_record_list(loaded['Records'])

    def load_from_record_list(self, records: List[Dict]):

        # Parse the raw record data into a set of EventRecord objects, mapped by event ID.
        self.records = algorithms.parse_record_list(records)

        # Process the events to make sure all bounds are well-defined.
        algorithms.normalize_events(self.records)

        # Determine the entire relevant time span, from the earliest start.min to the latest end.max.
        for rec in self.records.values():

            # Just pull all bounds into a list. We could look at only start.min and end.max, but we
            # want to catch the case where e.g. the earliest possible known date is an end boundary.
            bounds = [rec.start.min, rec.start.max, rec.end.min, rec.end.max]

            # We only want to track real dates - so ignore non-dates (infinities) in the normalized records.
            bounds = [b for b in bounds if type(b) is TimePoint]

            for bound in bounds:
                if self.min == -math.inf or bound < self.min:
                    self.min = bound
                if self.max == math.inf or bound > self.max:
                    self.max = bound

        if type(self.min) is not TimePoint:  # min and max be the same, but if one is real the other should be also.
            raise IncoherentTimelineError("[timeline.load] Failed to find any well-defined dates")

    def get_records(self) -> Dict[str, EventRecord]:
        return self.records
