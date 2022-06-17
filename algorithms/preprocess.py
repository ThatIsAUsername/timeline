
from typing import Dict, List
from data_types import EventRecord, EventData
from .construct import construct_records


def preprocess_event_data(data_list: List[EventData]) -> List[EventData]:
    """
    Auto-generate an event ID for any entry that lacks one.
    If multiple events are given the same explicit id, merge them together.

    Args:
        data_list: A list of EventData objects.

    Returns:
        The final list of preprocessed EventData objects.
    """
    # Put all records with explicit IDs at the start of the list.
    # This will ensure that auto-generated IDs don't interfere.
    records_with_ids = [rec for rec in data_list if rec.id]
    records_without_ids = [rec for rec in data_list if not rec.id]
    ordered_list = records_with_ids + records_without_ids

    # Loop through all EventData objects and ensure they all have an id, merging duplicates.
    processed_records = {}
    for rr in ordered_list:
        # If the record has no 'id' specified, generate one.
        if not rr.id:
            name_tokens = rr.name.split()
            rid = ''.join([tok[0].lower() for tok in name_tokens])

            # Make sure we don't already have a record with that ID.
            final_id = rid
            deconflict = 2
            while final_id in processed_records:
                final_id = rid + str(deconflict)
                deconflict += 1

            rr.id = final_id
        else:
            # If there is an explicit id, and it already
            # exists, then merge the two event records.
            rec_id = rr.id
            if rec_id in processed_records:
                processed_records[rec_id].merge(rr)
                rr.id = None  # Remove the duplicate's id so we can prune it.

        processed_records[rr.id] = rr

    # Filter the processed records into a final list to prune
    # duplicates and maintain the initial ordering.
    final_list = [dat for dat in data_list if dat.id]
    return final_list


def build_record_list(data_list: List[EventData]) -> Dict[str, EventRecord]:
    pre_datas = preprocess_event_data(data_list)
    records = construct_records(pre_datas)
    return records
