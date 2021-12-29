import math
from typing import Dict, Tuple
from collections import deque
from datetime import date

from data_types import EventRecord, TimeReference


def normalize_events(records: Dict[str, EventRecord], verbose: bool = True) -> Dict[str, EventRecord]:
    """
    Populate the min and max field for the start and end TimeReference for each EventRecord, using
        the other TimeRecords to provide the needed context.
    The passed-in record-list entries are modified in place, and the collection is returned as well.

    Args:
        records: a Dict of EventRecord IDs to the record objects.
        verbose: If true, log detailed information about the process.

    Returns:
        The record list after all dates have been made concrete to the extent possible.
    """
    for rec_id in records:
        if verbose:
            print(f"[normalize_event_list] Normalizing {rec_id}")
        normalize_event(rec_id=rec_id, records=records, verbose=verbose)
        # is min not set?
        #   Throw rid into stack
        #   get after refs, append to stack also
        #   for
        # is max set?
    # Pull first event.
    # Check min
    return records


def normalize_event(rec_id: str, records: Dict[str, EventRecord], verbose: bool = True):
    stack = deque()
    stack.append(rec_id)
    while len(stack) > 0:
        cid = stack.pop()
        if verbose:
            print(f"[normalize_event] checking bounds for {cid}")

        date_found = bind_reference_boundary(cid=cid,
                                             bind_start=True,
                                             bind_min=True,
                                             records=records,
                                             stack=stack,
                                             verbose=verbose)
        if not date_found:
            continue  # We didn't have enough info to pin this down, but stack should be updated. Loop again.

        date_found = bind_reference_boundary(cid=cid,
                                             bind_start=True,
                                             bind_min=False,
                                             records=records,
                                             stack=stack,
                                             verbose=verbose)
        if not date_found:
            continue  # We didn't have enough info to pin this down, but stack should be updated. Loop again.

        date_found = bind_reference_boundary(cid=cid,
                                             bind_start=False,
                                             bind_min=True,
                                             records=records,
                                             stack=stack,
                                             verbose=verbose)
        if not date_found:
            continue  # We didn't have enough info to pin this down, but stack should be updated. Loop again.

        date_found = bind_reference_boundary(cid=cid,
                                             bind_start=False,
                                             bind_min=False,
                                             records=records,
                                             stack=stack,
                                             verbose=verbose)
    if verbose:
        print(f"[normalize_event] Finished normalizing {rec_id}")


def bind_reference_boundary(cid: str,
                            bind_start: bool,  # True to bind start, False to bind end.
                            bind_min: bool,  # True to find min bound, False to find max.
                            records: Dict[str, EventRecord],
                            stack: deque,
                            verbose: bool = True) -> bool:
    """
    Do all the work necessary to bind a firm date to one boundary of a TimeReference in an EventRecord.
    Args:
        cid: The ID of the EventRecord to process.
        bind_start: True if we want to find a boundary for the `start` TimeReference, False to bind the `end`.
        bind_min: True to bind the TimeReference's `min` boundary, False to find the `max` boundary.
        records: A Dict of records, as received from parse_record_list.
        stack: A stack used for bookkeeping. If we can't resolve cid due to a dependence on some other record oid,
                then we push cid back into the stack, along with oid for further processing.
        verbose: If True, print out information about the process as we go.

    Returns:
        Whether we were able to determine the given bound.
        A return value of False can mean that we need to bind dates for another EventRecord before we can bind
            this one (in which case we will put cid and the relevant other record ID into `stack`) or it could mean
            it is impossible to determine with the information we have (in which case `stack` will not be modified).
    """

    rec = records[cid]
    cref: TimeReference = rec.start if bind_start else rec.end
    boundary: date = cref.min if bind_min else cref.max
    if boundary is not None:
        return True  # This boundary is already known; no work required.

    # Description of what we are binding for printouts.
    desc = f"{'start' if bind_start else 'end'}.{'min' if bind_min else 'max'}"

    # Rough outline of what this does, e.g. when finding start.min:
    # Retrieve start reference's 'older' constraints
    # Create temp list of resolved constraints
    # for each constraint:
    #   if a date, add to temp list
    #   if a ref, fetch the ref.
    #     if the ref's end min is defined, add it to temp list (respecting $ and ^ modifiers).
    #     if the ref's end min is not defined, push rec and the ref into stack, and return False
    # Temp list should have only resolved dates now. Choose the latest one as start, and return True

    # Get the set of relevant constraints.
    constraints = cref._older_refs if bind_min else cref._later_refs
    resolved_constraints = []
    for constraint in constraints:
        if type(constraint) is date:
            resolved_constraints.append(constraint)
        elif type(constraint) is str:
            fix_begin = constraint[0] == '$'
            fix_end = constraint[-1] == '^'
            constraint_id = constraint.strip('$^')

            if constraint_id not in records:  # Sanity check.
                print(f"[bind_reference_boundary] ERROR: Record {cid} references unknown record {constraint_id}. Skipping")
                return False

            constraint_record = records[constraint_id]
            # if bind_min:
            # $old_ref - cref's min must be no earlier than constraint_record's start.min
            # old_ref^ - cref's min must be no earlier than constraint_record's end.min
            # old_ref - cref's min must be no earlier than constraint_record's end.min
            # if not bind_min:
            # $old_ref - cref's max must be no later than constraint_record's start.max
            # old_ref^ - cref's max must be no later than constraint_record's end.max
            # old_ref - cref's max must be no later than constraint_record's start.max
            if bind_min:  # if binding a min, a ^ (end-of-range) bound is the same as no bound.
                relevant_boundary = constraint_record.start.min if fix_begin else constraint_record.end.min
            else:  # if binding a max, a $ (start-of-range) bound is the same as no bound.
                relevant_boundary = constraint_record.end.max if fix_end else constraint_record.start.max

            if relevant_boundary is None:  # The other records dates are not yet known.
                stack.append(cid)  # Put the current record ID back on the stack for now.
                stack.append(constraint_id)  # Also push this constraining record onto the stack to figure out first.
                if verbose:
                    print(f"[bind_reference_boundary] Record {cid} references unprocessed record {constraint_id}. Delaying.")
                return False  # We don't have enough info yet. Hold off for now.
            else:  # The other record's relevant date is known; hold onto it.
                resolved_constraints.append(relevant_boundary)  # This should either be a date or +/-inf.
                if verbose:
                    print(f"[bind_reference_boundary] Record {cid}.{desc} must be {'after' if bind_min else 'before'} "
                          f"{constraint_id}{'.start' if fix_begin else '.end' if fix_end else ''}."
                          f"{'min' if bind_min else 'max'} ({relevant_boundary})")

    # If we made it this far, then resolved_constraints should be a list of dates, and maybe some +/-infinities.
    bind_value = None
    if len(resolved_constraints) == 0:
        # Unconstrained boundaries are just set to the extremes.
        bind_value = -math.inf if bind_min else math.inf
        if verbose:
            print(f"[bind_reference_boundary] No constraints defined for {cid}'s {desc}. Setting to {bind_value}.")
    elif len(resolved_constraints) == 1:
        bind_value = resolved_constraints[0]
        if verbose:
            print(f"[bind_reference_boundary] Setting {cid}'s {desc} to {bind_value}")
    else:
        # Constraints can be a date or +/-inf if the constraining ref was itself unconstrained.
        # Ignore non-dates if any dates exist.
        real_dates = [real for real in resolved_constraints if type(real) is date]
        if len(real_dates) == 0:
            bind_value = resolved_constraints[0]  # Only possibility here should be +/-math.inf.
            if verbose:
                print(f"[bind_reference_boundary] No real constraints found for {cid}'s {desc}. Setting to {bind_value}.")
        else:
            # Choose the best available constraint as our current bound.
            bind_value = max(real_dates) if bind_min else min(real_dates)
            if verbose:
                print(f"[bind_reference_boundary] {cid}'s {desc} set to {bind_value}")

    # At this point, we should have properly defined bind_value as a date or as -math.inf.
    assert bind_value is not None, f'Failed to set {desc} for {cid}!'
    if bind_min:
        cref.min = bind_value
    else:
        cref.max = bind_value
    return True
