
from typing import Dict
from data_types import EventRecord


def parse_record_list(record_list) -> Dict[str, EventRecord]:
    """
    Turn a parsed yaml structure into a dict of EventRecord objects, keyed by their event ids.
    Auto-generates a record ID for any record that lacks one.

    Args:
        record_list: A list of event records freshly-loaded from a yaml data file.

    Returns:
        A dict of record IDs to the corresponding EventRecord objects.
    """

    final_dict = {}
    for rr in record_list:
        # If the record has no 'id' specified, generate one.
        if 'id' not in rr:
            name_tokens = rr['name'].split()
            rid = ''.join([tok[0].lower() for tok in name_tokens])

            # Make sure we don't already have a record with that ID.
            final_id = rid
            deconflict = 2
            while final_id in final_dict:
                final_id = rid + str(deconflict)
                deconflict += 1

            rr['id'] = final_id

        rid = rr['id']
        record = EventRecord(rr)

        final_dict[rid] = record

    return final_dict
