
import re
import math
from typing import Dict, List
from collections import deque

from data_types import EventRecord, EventData, TimeReference, TimePoint, InconsistentTimeReferenceError, UnknownEventRecordError, TimeSpan
from logs import get_logger


def construct_records(event_datas: List[EventData]) -> Dict[str, EventRecord]:
    """
    Convert all the EventData objects into EventRecords with resolved boundaries.
    Populate the min and max field for the start and end TimeReference for each EventRecord, using
        the other events to provide the needed context.

    Args:
        event_datas: A List of preprocessed EventData objects

    Returns:
        The record list after all dates have been made concrete to the extent possible.
    """
    algo_logger = get_logger()

    # Construct EventRecords from the EventData objects, then reconcile their start/end bounds.
    records: Dict[str, EventRecord] = {evt_dat.id: EventRecord(evt_dat) for evt_dat in event_datas}

    resolved = []
    for rec_id in records:
        if rec_id in resolved:
            # If this record was already done on a previous pass (because another record
            # refers to it) then don't bother trying to reprocess it.
            continue
        algo_logger.debug(f"Normalizing `{rec_id}`")
        dones = reconcile_record_bounds(rec_id=rec_id, records=records)
        resolved.extend(dones)

    return records


def reconcile_record_bounds(rec_id: str, records: Dict[str, EventRecord]) -> List[str]:
    """
    Determine fixed dates for all TimeReference boundaries for event rec_id.
    This may require recursively resolving bounds for any other events this one references.

    Args:
        rec_id: ID of the EventRecord to resolve.
        records: Dict of all EventRecords for reference.

    Returns:
        A list of all recursively-resolved events so we can avoid extra calls?
    """
    algo_logger = get_logger()
    stack = deque()
    stack.append(rec_id)
    resolved = []
    while len(stack) > 0:
        cid = stack.pop()
        algo_logger.debug(f"Checking bounds for `{cid}`")

        date_found = bind_reference_boundary(cid=cid,
                                             bind_start=True,
                                             bind_min=True,
                                             records=records,
                                             stack=stack)
        if not date_found:
            continue  # We didn't have enough info to pin this down, but stack should be updated. Loop again.

        date_found = bind_reference_boundary(cid=cid,
                                             bind_start=True,
                                             bind_min=False,
                                             records=records,
                                             stack=stack)
        if not date_found:
            continue  # We didn't have enough info to pin this down, but stack should be updated. Loop again.

        date_found = bind_reference_boundary(cid=cid,
                                             bind_start=False,
                                             bind_min=True,
                                             records=records,
                                             stack=stack)
        if not date_found:
            continue  # We didn't have enough info to pin this down, but stack should be updated. Loop again.

        date_found = bind_reference_boundary(cid=cid,
                                             bind_start=False,
                                             bind_min=False,
                                             records=records,
                                             stack=stack)
        if not date_found:
            continue  # We didn't have enough info to pin this down, but stack should be updated. Loop again.

        # We've set start min/max and end min/max. Now enforce internal consistency.
        # We can't define these relations in advance because that would create recursive dependencies.
        cur = records[cid]

        # Make sure the start can't be later than the end.
        if type(cur.start.max) is float or\
                (type(cur.start.max) is TimePoint and type(cur.end.max) is TimePoint and cur.start.max > cur.end.max):
            cur.start.max = cur.end.max  # Can't start later than the latest possible end time (could still be inf).
            algo_logger.debug(f"Setting `{cid}` start.max to respect `{cid}` end.max ({cur.start.max}).")

        if type(cur.start.min) is TimePoint and type(cur.start.max) is TimePoint and cur.start.min > cur.start.max:
            raise InconsistentTimeReferenceError(f"start.min of `{cid}` ({cur.start.min}) is after start.max ({cur.start.max}).")

        # Make sure the end can't be earlier than the start.
        if not cur.end.has_min() or \
                (cur.end.has_min() and cur.start.has_min() and cur.end.min < cur.start.min):
            cur.end.min = cur.start.min  # End can't be before the earliest possible start time (could still be -inf).
            algo_logger.debug(f"Setting `{cid}` end.min to respect `{cid}` start.min ({cur.end.min}).")

        # We can't handle duration in bind_reference_boundary because it is a self-referential dependency. Do it here.
        if cur.duration:
            bind_duration(cur)

        if cur.end.has_min() and cur.end.has_max() and cur.end.min > cur.end.max:
            raise InconsistentTimeReferenceError(f"end.min of `{cid}` ({cur.end.min}) is after end.max ({cur.end.max}).")

        # This record is now done; we don't have to redo it on a future pass.
        resolved.append(cid)
        algo_logger.debug(f"Finished normalizing `{cid}`")

    return resolved


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
    algo_logger = get_logger()
    rec = records[cid]
    cref: TimeReference = rec.start if bind_start else rec.end
    boundary: TimePoint = cref.min if bind_min else cref.max
    if boundary is not None:
        return True  # This boundary is already known; no work required.

    # Description of what we are binding for printouts.
    desc = f"{cid}.{'start' if bind_start else 'end'}.{'min' if bind_min else 'max'}"

    algo_logger.debug(f"Binding {desc} to a concrete date.")

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
        algo_logger.debug(f"Processing constraint '{constraint}'")
        if type(constraint) is TimePoint:
            resolved_constraints.append(constraint)
        elif type(constraint) is str:
            # If '+' or '-' is present, split on it and then parse the offset.
            offset = None
            if '+' in constraint or '-' in constraint:
                sign = -1 if '-' in constraint else 1
                constraint, offset_str = re.split('[+-]+', constraint)
                constraint, offset_str = constraint.strip(), offset_str.strip()
                offset = TimeSpan.parse(offset_str)
                if sign == -1:
                    offset.invert()

            # Resolve the primary constraint if possible.
            fix_end = constraint[-1] == '$'
            fix_begin = constraint[0] == '^'
            constraint_id = constraint.strip('^$')

            if constraint_id not in records:  # Sanity check.
                raise UnknownEventRecordError(f"Record {cid} references unknown record '{constraint_id}'.")

            constraint_record = records[constraint_id]
            # if bind_min:
            # ^old_ref - cref's min must be no earlier than constraint_record's start.min
            # old_ref$ - cref's min must be no earlier than constraint_record's end.min
            # old_ref - cref's min must be no earlier than constraint_record's end.min
            # if not bind_min:
            # ^old_ref - cref's max must be no later than constraint_record's start.max
            # old_ref$ - cref's max must be no later than constraint_record's end.max
            # old_ref - cref's max must be no later than constraint_record's start.max
            constraint_desc = ''
            if bind_min:  # if binding a min, a ^ (end-of-range) bound is the same as no bound.
                relevant_boundary = constraint_record.start.min if fix_begin else constraint_record.end.min
                constraint_desc = f"{constraint_id}.start.min" if fix_begin else f"{constraint_id}.end.min"
            else:  # if binding a max, a $ (start-of-range) bound is the same as no bound.
                relevant_boundary = constraint_record.end.max if fix_end else constraint_record.start.max
                constraint_desc = f"{constraint_id}.end.max" if fix_begin else f"{constraint_id}.start.max"

            if relevant_boundary is None:  # The other records dates are not yet known.
                stack.append(cid)  # Put the current record ID back on the stack for now.
                stack.append(constraint_id)  # Also push this constraining record onto the stack to figure out first.
                algo_logger.debug(f"Record '{cid}' references unprocessed record '{constraint_id}'. Delaying.")
                return False  # We don't have enough info yet. Hold off for now.
            else:  # The other record's relevant date is known; hold onto it.
                # If there is an offset, add it to the relevant_boundary before storing. Not applicable for +/-inf.
                if offset and type(relevant_boundary) is TimePoint:
                    algo_logger.debug(f"Offsetting {relevant_boundary} by {offset}")
                    relevant_boundary = relevant_boundary + offset
                resolved_constraints.append(relevant_boundary)  # This should either be a date or +/-inf.
                algo_logger.debug(f"{desc} must be {'after' if bind_min else 'before'}"
                                  f" {relevant_boundary} ({constraint_desc} + {offset}).")

    # If we made it this far, then resolved_constraints should be a list of dates, and maybe some +/-infinities.
    bind_value = None
    if len(resolved_constraints) == 0:
        # Unconstrained boundaries are just set to the extremes.
        bind_value = -math.inf if bind_min else math.inf
        algo_logger.debug(f"No constraints defined for {desc}. Setting to {bind_value}.")
    elif len(resolved_constraints) == 1:
        bind_value = resolved_constraints[0]
        algo_logger.debug(f"Setting {desc} to {bind_value}")
    else:
        # Constraints can be a date or +/-inf if the constraining ref was itself unconstrained.
        # Ignore non-dates if any dates exist.
        real_dates = [real for real in resolved_constraints if type(real) is TimePoint]
        if len(real_dates) == 0:
            bind_value = resolved_constraints[0]  # Only possibility here should be +/-math.inf.
            algo_logger.debug(f"No real constraints found for {desc}. Setting to {bind_value}.")
        else:
            # Choose the best available constraint as our current bound.
            bind_value = max(real_dates) if bind_min else min(real_dates)
            algo_logger.debug(f"{desc} set to {bind_value}")

    # At this point, we should have properly defined bind_value as a date or as -math.inf.
    assert bind_value is not None, f"Failed to set {desc}!"
    if bind_min:
        cref.min = bind_value
    else:
        cref.max = bind_value
    return True


def bind_duration(cur: EventRecord):
    algo_logger = get_logger()
    cid = cur.id
    dur: TimeSpan = cur.duration

    # If we know the start and not the end or vice versa, we can use one to bound the other.
    if cur.start.has_min() and not cur.end.has_min():
        algo_logger.debug(f"Setting end.min to start.min+duration: {cur.end.min} + {dur}")
        cur.end.min = cur.start.min + dur
        algo_logger.debug(f"New end.min: {cur.end.min}")
    if not cur.start.has_min() and cur.end.has_min():
        algo_logger.debug(f"Setting start.min to end.min-duration: {cur.start.min} - {dur}")
        cur.start.min = cur.end.min - dur
        algo_logger.debug(f"New start.min: {cur.start.min}")
    if cur.start.has_max() and not cur.end.has_max():
        algo_logger.debug(f"Setting end.max to start.max+duration: {cur.end.max} + {dur}")
        cur.end.max = cur.start.max + dur
        algo_logger.debug(f"New end.max: {cur.end.max}")
    if not cur.start.has_max() and cur.end.has_max():
        algo_logger.debug(f"Setting start.max to end.max-duration: {cur.end.max} - {dur}")
        cur.start.max = cur.end.max - dur
        algo_logger.debug(f"New start.max: {cur.start.max}")

    # For a given event record which starts between S1 and S2, ends between E1 and E2, and has duration D:
    # Then these constraints must hold: A1 + D = E1, and A2 + D = E2
    #        |------------D-------------|
    #    A1 - - - - - A2-------------E1 - - - - - E2
    # Thus:
    # If A1 + D < E1, then increase A1 until A1 + D == E1.
    # If A1 + D > E1, then increase E1 until A1 + D == E1.
    # If A2 + D > E2, then decrease A2 until A2 + D == E2.
    # If A2 + D < E2, then decrease E2 until A2 + D == E2.
    # If A1 + D > E2, then this TimePoint is inconsistent.
    # If A2 + D < E1, then this TimePoint is inconsistent.
    a1: TimePoint = cur.start.min if cur.start.has_min() else None
    a2: TimePoint = cur.start.max if cur.start.has_max() else None
    e1: TimePoint = cur.end.min if cur.end.has_min() else None
    e2: TimePoint = cur.end.max if cur.end.has_max() else None

    if a1 and e1:
        a1_d = a1 + dur
        if a1_d < e1:
            a1 = e1 - dur
            algo_logger.debug(f"Shifting start.min right to {a1}")
        elif a1_d > e1:
            e1 = a1_d
            algo_logger.debug(f"Shifting end.min right to {e1}")

    if a2 and e2:
        a2_d = a2 + dur
        if a2_d > e2:
            a2 = e2 - dur
            algo_logger.debug(f"Shifting start.max right to {a2}")
        elif a2_d < e2:
            e2 = a2_d
            algo_logger.debug(f"Shifting end.max left to {e1}")

    # Ensure durations are internally consistent.
    if a1 and e2 and a1 + dur > e2:
        raise InconsistentTimeReferenceError(f"Duration of event '{cur.name}' ({cid}) is inconsistent with the start and end minimums!")
    if a2 and e1 and a2 + dur < e1:
        raise InconsistentTimeReferenceError(f"Duration of event '{cur.name}' ({cid}) is inconsistent with the start and end maximums!")

    # Assign our new and improved bounds back to the TimeReference.
    cur.start.min = a1 if a1 else -math.inf
    cur.start.max = a2 if a2 else math.inf
    cur.end.min = e1 if e1 else -math.inf
    cur.end.max = e2 if e2 else math.inf
