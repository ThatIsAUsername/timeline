
from typing import Dict, List
from data_types import EventRecord


def parse_record_list(record_list: List[Dict]) -> Dict[str, EventRecord]:
    """
    Turn a parsed yaml structure into a dict of EventRecord objects, keyed by their event ids.
    Auto-generates a record ID for any record that lacks one.

    Args:
        record_list: A list of event records freshly-loaded from a yaml data file.

    Returns:
        A dict of record IDs to the corresponding EventRecord objects.
    """
    records_with_ids = [rec for rec in record_list if 'id' in rec]
    records_without_ids = [rec for rec in record_list if 'id' not in rec]
    ordered_list = records_with_ids + records_without_ids

    final_dict = {}
    for rr in ordered_list:
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
        else:
            # If there is an explicit id, and it already
            # exists, then merge the two event records.
            rec_id = rr['id']
            if rec_id in final_dict:
                final_dict[rec_id].merge(rr)

        rid = rr['id']
        record = EventRecord(rr)

        final_dict[rid] = record

    return final_dict
