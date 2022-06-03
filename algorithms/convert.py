
from typing import Dict, List
from data_types import EventRecord, EventData


def parse_record_list(record_list: List[EventData]) -> Dict[str, EventRecord]:
    """
    Turn a parsed yaml structure into a dict of EventRecord objects, keyed by their event ids.
    Auto-generates a record ID for any record that lacks one.

    Args:
        record_list: A list of event records freshly-loaded from a yaml data file.

    Returns:
        A dict of record IDs to the corresponding EventRecord objects.
    """
    # Put all records with explicit IDs at the start of the list.
    # This will ensure that auto-generated IDs don't interfere.
    records_with_ids = [rec for rec in record_list if rec.id]
    records_without_ids = [rec for rec in record_list if not rec.id]
    ordered_list = records_with_ids + records_without_ids

    # Loop through all EventData objects and ensure they all have an id, merging duplicates.
    final_dict = {}
    for rr in ordered_list:
        # If the record has no 'id' specified, generate one.
        if not rr.id:
            name_tokens = rr.name.split()
            rid = ''.join([tok[0].lower() for tok in name_tokens])

            # Make sure we don't already have a record with that ID.
            final_id = rid
            deconflict = 2
            while final_id in final_dict:
                final_id = rid + str(deconflict)
                deconflict += 1

            rr.id = final_id
        else:
            # If there is an explicit id, and it already
            # exists, then merge the two event records.
            rec_id = rr.id
            if rec_id in final_dict:
                rr.merge(final_dict[rec_id])

        final_dict[rr.id] = rr

    # Construct EventRecords from the EventData objects.
    return_dict = {evt_id: EventRecord(evt_dat) for evt_id, evt_dat in final_dict.items()}
    return return_dict
