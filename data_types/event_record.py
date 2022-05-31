
from typing import Dict, List, Tuple, Union
from data_types import TimeReference, TimeSpan


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

    def merge(self, record_data: Dict):
        """
        Combine the data/constraints in `record_data` with what is already in this record.
        Raise an error if the new record materially differs from the current data.

        Args:
            record_data: A dict generated from a record loaded from a yaml data file.
        """
        if self.id != record_data['id']:
            raise ValueError(f"Attempted to merge record {record_data['id']} into record {self.id}!")

        # Merge the new data into the existing raw record dict.
        self._data.update(record_data)

        # Update the TimeReferences with any new constraints.
        start, start_after, start_before = self._extract_time_refs(record_data, start_refs=True)
        end, end_after, end_before = self._extract_time_refs(record_data, start_refs=False)
        self.start.merge(start, start_after, start_before)
        self.end.merge(end, end_after, end_before)

        new_duration = self._extract_duration(record_data)
        if self.duration and new_duration and new_duration != self.duration:
            raise ValueError(f"Record {self.id} with duration {self.duration} has conflicting new duration {new_duration}")
        self.duration = new_duration  # Replace in case old duration is None and new is specified.

        new_sources: List = record_data['sources'] if 'sources' in record_data else []
        self.sources.extend(new_sources)

    @staticmethod
    def _extract_time_refs(record_data: Dict, start_refs: bool) -> Tuple:
        key = "start" if start_refs else "end"
        aft_key, bef_key = f"{key}_after", f"{key}_before"

        absolute = record_data[key] if key in record_data else None
        after_data = record_data[aft_key] if aft_key in record_data else None
        before_data = record_data[bef_key] if bef_key in record_data else None

        return absolute, after_data, before_data

    @staticmethod
    def _extract_duration(record_data: Dict) -> Union[TimeSpan, None]:
        dur: str = record_data['duration'] if 'duration' in record_data else None
        if dur is None:
            return None
        return TimeSpan.parse(dur)

    def __str__(self):
        return self.name
