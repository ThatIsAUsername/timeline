from typing import Dict, List, Union
from dataclasses import dataclass

from logs import get_logger


@dataclass
class EventData:
    """
    Holds the data from a single EventRecord's input dictionary, and provides convenient accessors.
    """

    name: str = ''
    id: str = ''
    start: Union[str, List[str]] = ''
    end: Union[str, List[str]] = ''
    start_before: Union[str, List[str]] = ''
    end_before: Union[str, List[str]] = ''
    start_after: Union[str, List[str]] = ''
    end_after: Union[str, List[str]] = ''
    duration: str = ''
    info: Union[str, List[str]] = ''

    @staticmethod
    def parse(event_record: Dict) -> 'EventData':

        ss = event_record.get('start', [])
        ee = event_record.get('end', [])
        sb = event_record.get('start_before', [])
        sa = event_record.get('start_after', [])
        eb = event_record.get('end_before', [])
        ea = event_record.get('end_after', [])
        nf = event_record.get('info', [])
        # Just wrap everything that can be a list, as a list, for consistency.
        ss, ee, sb, sa, eb, ea, nf = [
            [bound] if not isinstance(bound, list) else bound
            for bound in [ss, ee, sb, sa, eb, ea, nf]
        ]

        return EventData(name=event_record.get('name', None),
                         id=event_record.get('id', None),
                         start=ss,
                         end=ee,
                         start_before=sb,
                         start_after=sa,
                         end_before=eb,
                         end_after=ea,
                         duration=event_record.get('duration', None),
                         info=nf)

    def merge(self, other: 'EventData'):
        """
        Combine data from another EventData object with the same id into this object to consolidate constraints.
        Args:
            other: Another EventData object with the same ID as this one.

        Returns:
            None

        Raises: ValueError if `other` has a different record ID or duration. If other attributes create
            a conflict, this will be discovered when the event boundaries are reconciled.
        """
        if self.name != other.name:
            log = get_logger()
            log.warning(f"Event {self.name} is merging with a differently-named event {other.name}")
        if self.id != other.id:
            raise ValueError(f"Trying to merge event data for {other.id} into data for {self.id}!")
        if self.duration and other.duration and self.duration != other.duration:
            raise ValueError(f"Record {self.id} is defined with two conflicting durations ({self.duration} and {other.duration})!")
        self.duration = other.duration if not self.duration else self.duration  # Keep if specified, replace if not.

        def combine_lists(list1: List[str], list2: List[str]) -> List[str]:
            combined = list1 + list2
            return list(set(combined))

        self.start = combine_lists(self.start, other.start)
        self.end = combine_lists(self.end, other.end)
        self.start_before = combine_lists(self.start_before, other.start_before)
        self.end_before = combine_lists(self.end_before, other.end_before)
        self.start_after = combine_lists(self.start_after, other.start_after)
        self.end_after = combine_lists(self.end_after, other.end_after)
        self.info = combine_lists(self.info, other.info)
