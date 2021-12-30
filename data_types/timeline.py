from typing import Dict
import yaml

from algorithms import parse_record_list
from algorithms import normalize_events


class Timeline:
    def __init__(self):
        self.records = {}  # Map record ID to record

    def load(self, filename: str):
        with open(filename) as file:
            loaded = yaml.load(file, Loader=yaml.BaseLoader)

        # Sources should just load as a dict.
        self.records = parse_record_list(loaded['Records'])

        # Process the events to make sure all bounds are well-defined.
        normalize_events(self.records)

    def get_records(self) -> Dict:
        return self.records
