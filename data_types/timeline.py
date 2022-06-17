from typing import Dict, List, Union
import yaml
import math

from data_types import EventRecord, TimePoint, IncoherentTimelineError, EventData
from logs import get_logger
import algorithms


class Timeline:
    def __init__(self):
        self.records = {}  # Map record ID to record
        self.min = -math.inf
        self.max = math.inf

    def load_records(self, inputs: Union[str, List[str]]):
        """
        Load record entries from one or more files to initialize this timeline.
        If multiple files contain records with the same explicitly-set id, they
        will be treated as the same event.

        Args:
            inputs: Either a filename or a list of filenames containing event records.
        """
        # Wrap in a list if needed to simplify the following logic.
        if type(inputs) is str:
            inputs = [inputs]

        # Load all records from all provided files into one record list.
        # Any duplicates will be reconciled in a later step.
        dict_list = []
        for filename in inputs:
            with open(filename) as file:
                loaded = yaml.load(file, Loader=yaml.BaseLoader)
                dict_list.extend(loaded['Records'])

        event_datas: List[EventData] = [EventData.parse(rr) for rr in dict_list]
        self.init_from_event_data(event_datas)

    def init_from_event_data(self, event_datas: List[EventData], *, recursing=False):

        # Generate EventRecords with consistent boundaries based on the data we read in.
        self.records: Dict[str, EventRecord] = algorithms.build_record_list(event_datas)

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

        if not recursing and type(self.min) is not TimePoint:
            # If we weren't able to anchor anything so far, then nail down the first event to start at 0 and retry.
            logger = get_logger()
            logger.warn(f"Unable to resolve any well-defined dates on first pass. Fixing '{event_datas[0].name}' to start at 1 Jan 0")
            event_datas[0].start.append('1 Jan 0')
            self.init_from_event_data(event_datas, recursing=True)
        if type(self.min) is not TimePoint:
            raise IncoherentTimelineError("[timeline.load] Failed to find any well-defined dates")

    def get_records(self) -> Dict[str, EventRecord]:
        return self.records
