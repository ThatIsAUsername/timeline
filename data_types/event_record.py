
from typing import List, Tuple, Union
from data_types import TimeReference, TimeSpan, EventData


class EventRecord:
    def __init__(self, record_data: EventData):
        """
        Represents a range of time. The beginning and end are represented by TimeReference objects, and may have
            uncertainty, e.g.: The Roman empire existed from 27 BC through sometime between 395 and 1453 AD.
        Args:
            record_data: An EventData object characterising this record.
        """
        # name/id, start, end, source, extra info and #tags, references
        self._data: EventData = record_data
        self.name: str = record_data.name
        self.id: str = record_data.id
        start, start_after, start_before = self._extract_time_refs(record_data, start_refs=True)
        end, end_after, end_before = self._extract_time_refs(record_data, start_refs=False)
        self.start: TimeReference = TimeReference(absolutes=start,
                                                  older=start_after,
                                                  later=start_before)
        self.end: TimeReference = TimeReference(absolutes=end,
                                                older=end_after,
                                                later=end_before)
        self.duration = self._extract_duration(record_data)
        self.info: List[str] = record_data.info

    @staticmethod
    def _extract_time_refs(record_data: EventData, start_refs: bool) -> Tuple:
        if start_refs:
            absolute = record_data.start
            after_data = record_data.start_after
            before_data = record_data.start_before
        else:
            absolute = record_data.end
            after_data = record_data.end_after
            before_data = record_data.end_before

        return absolute, after_data, before_data

    @staticmethod
    def _extract_duration(record_data: EventData) -> Union[TimeSpan, None]:
        return TimeSpan.parse(record_data.duration) if record_data.duration else None

    def __str__(self):
        return self.name
