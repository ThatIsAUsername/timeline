
from typing import Dict, List
from data_types import EventRecord, EventData
from .construct import construct_records
from logs import get_logger


def preprocess_event_data(data_list: List[EventData]) -> Dict[str, EventData]:
    """
    Auto-generate an event ID for any entry that lacks one.
    If multiple events are given the same explicit id, merge them together.

    Args:
        data_list: A list of EventData objects.

    Returns:
        The final list of preprocessed EventData objects, mapped by id.
    """
    # Put all records with explicit IDs at the start of the list.
    # This will ensure that auto-generated IDs don't interfere.
    records_with_ids = [rec for rec in data_list if rec.id]
    records_without_ids = [rec for rec in data_list if not rec.id]
    ordered_list = records_with_ids + records_without_ids

    # Loop through all EventData objects and ensure they all have an id, merging duplicates.
    _logger = get_logger()
    processed_records: Dict[str, EventData] = {}
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
            processed_records[rr.id] = rr
        else:
            # If there is an explicit id, and it already
            # exists, then merge the two event records.
            if rr.id in processed_records:
                rr.merge(processed_records[rr.id])

            processed_records[rr.id] = rr

    # Filter the processed records into a final list to prune
    # duplicates and maintain the initial ordering.
    final_dict = {}
    for rec_id, rec in processed_records.items():
        if rec_id not in final_dict:
            final_dict[rec_id] = rec
    return final_dict


def build_record_list(data_list: List[EventData]) -> Dict[str, EventRecord]:
    pre_datas = preprocess_event_data(data_list)
    records = construct_records(pre_datas)
    return records
