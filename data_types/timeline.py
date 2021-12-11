from typing import Dict
import yaml


class Timeline:
    def __init__(self):
        self.records = {}  # Map record ID to record
        self.sources = {}  # Map source ID to source

    def load(self, filename: str):
        with open(filename) as file:
            loaded = yaml.safe_load(file)
        for rr in loaded['Records']:
            if 'id' in rr:
                rid = rr['id']
            else:
                # If the record has no 'id' specified, generate one.
                name_tokens = rr['name'].split()
                rid = ''.join([tok[0] for tok in name_tokens])
                final_id = rid

                # Make sure we don't already have a record with that ID.
                deconflict = 2
                while final_id in self.records:
                    final_id = rid + str(deconflict)
                    deconflict += 1
                rid = final_id
            self.records[rid] = rr

        # Sources should just load as a dict already.
        self.sources = loaded['Sources']

    def get_records(self) -> Dict:
        return self.records

    def get_sources(self) -> Dict:
        return self.sources


if __name__ == "__main__":
    tl = Timeline()
    tl.load("data/rev_war.yaml")

    for rec in tl.get_records().items():
        print(rec)
    for src in tl.get_sources().items():
        print(src)