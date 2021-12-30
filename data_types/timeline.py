from typing import Dict
import yaml

import algorithms


class Timeline:
    def __init__(self):
        self.records = {}  # Map record ID to record

    def load(self, filename: str):
        with open(filename) as file:
            loaded = yaml.load(file, Loader=yaml.BaseLoader)

        # Parse the raw record data into a set of EventRecord objects, mapped by event ID.
        self.records = algorithms.parse_record_list(loaded['Records'])

        # Process the events to make sure all bounds are well-defined.
        algorithms.normalize_events(self.records)

    def get_records(self) -> Dict:
        return self.records
