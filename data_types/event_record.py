
from typing import Dict, List, Tuple, Union
from data_types import TimeReference, EventDuration


class EventRecord:
    def __init__(self, record_data: Dict):
        """
        Represents a range of time. The beginning and end are represented by TimeReference objects, and may have
            uncertainty, e.g.: The Roman empire existed from 27 BC through sometime between 395 and 1453 AD.
        Args:
            record_data: A dict generated from a record loaded from a yaml data file.
        """
        # name/id, start, end, source, extra info and #tags, references
        self._data = record_data
        self.name: str = record_data['name']
        self.id: str = record_data['id']
        start, start_after, start_before = self._extract_time_refs(record_data, start_refs=True)
        end, end_after, end_before = self._extract_time_refs(record_data, start_refs=False)
        self.start: TimeReference = TimeReference(absolute=start,
                                                  older=start_after,
                                                  later=start_before)
        self.end: TimeReference = TimeReference(absolute=end,
                                                older=end_after,
                                                later=end_before)
        self.duration = self._extract_duration(record_data)
        self.sources: List = record_data['sources'] if 'sources' in record_data else []

    @staticmethod
    def _extract_time_refs(record_data: Dict, start_refs: bool) -> Tuple:
        key = "start" if start_refs else "end"
        aft_key, bef_key = f"{key}_after", f"{key}_before"

        absolute = record_data[key] if key in record_data else None
        after_data = record_data[aft_key] if aft_key in record_data else None
        before_data = record_data[bef_key] if bef_key in record_data else None

        return absolute, after_data, before_data

    @staticmethod
    def _extract_duration(record_data: Dict) -> Union[EventDuration, None]:
        dur: str = record_data['duration'] if 'duration' in record_data else None
        if dur is None:
            return None
        return EventDuration.parse(dur)

    def __str__(self):
        return self.name
