
from typing import Dict
import unittest
import math
import yaml

from algorithms import construct_records, preprocess_event_data, build_record_list
from data_types import EventRecord, EventData, TimePoint, InconsistentTimeReferenceError, UnknownEventRecordError
from calendar import month_abbr

months = list(month_abbr)


class TestNormalizeEvents(unittest.TestCase):

    def test_simple_case(self):

        # Arrange
        record_list = [{'name': 'Life', 'id': 'life', 'start': 'birth', 'end': 'death'},
                       {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                       {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'},
                       ]
        birth_date = TimePoint(day=17, month=months.index('Aug'), year=1970)
        death_date = TimePoint(day=5, month=months.index('Jun'), year=2040)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), 3)
        self.assertIn('life', records)
        self.assertIn('birth', records)
        self.assertIn('death', records)
        self.assertEqual(records['life'].start.min, birth_date)
        self.assertEqual(records['life'].start.max, birth_date)
        self.assertEqual(records['life'].end.min, death_date)
        self.assertEqual(records['life'].end.max, death_date)

    def test_simple_case_unbounded(self):

        # Arrange
        # This is the same as test_simple_case, but now we use start_before and end_after.
        record_list = [{'name': 'Life', 'id': 'life', 'start_before': 'birth', 'end_after': 'death'},
                       {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                       {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'},
                       ]
        birth_date = TimePoint(day=17, month=months.index('Aug'), year=1970)
        death_date = TimePoint(day=5, month=months.index('Jun'), year=2040)
        start_ans = -math.inf
        end_ans = math.inf

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), 3)
        self.assertIn('life', records)
        self.assertIn('birth', records)
        self.assertIn('death', records)
        self.assertEqual(records['life'].start.min, start_ans)
        self.assertEqual(records['life'].start.max, birth_date)
        self.assertEqual(records['life'].end.min, death_date)
        self.assertEqual(records['life'].end.max, end_ans)

    def test_unbounded_record(self):

        # Arrange
        rec_id = 'eternity'
        record_list = [{'name': 'Eternity', 'id': rec_id}]
        rec_beg = -math.inf
        rec_end = math.inf

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), 1)
        self.assertIn(rec_id, records)

        # The record has no time constraints, so start and end could be anytime.
        rec = records[rec_id]
        self.assertEqual(rec.start.min, rec_beg)
        self.assertEqual(rec.start.max, rec_end)
        self.assertEqual(rec.end.min, rec_beg)
        self.assertEqual(rec.end.max, rec_end)

    def test_end_only(self):

        # Arrange
        rec_id = 'eternity_past'
        record_list = [{'name': 'Eternity past', 'id': rec_id, 'end': '5 Jun 2040'}]
        rec_beg = -math.inf
        rec_end = TimePoint(day=5, month=months.index('Jun'), year=2040)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), 1)
        self.assertIn(rec_id, records)

        # The record has no time constraints, so start and end could be anytime.
        rec = records[rec_id]
        self.assertEqual(rec.start.min, rec_beg)
        self.assertEqual(rec.start.max, rec_end)
        self.assertEqual(rec.end.min, rec_end)
        self.assertEqual(rec.end.max, rec_end)

    def test_end_before_start(self):

        # Arrange
        # Set up an impossible timeline:  <------end-----| June 5 | June 6 |-----start------>
        rec_id = 'broken'
        record_list = [{'name': 'Broken', 'id': rec_id, 'start_after': '6 Jun 2040', 'end_before': '5 Jun 2040'}]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        with self.assertRaises(InconsistentTimeReferenceError) as context:
            records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertIn(rec_id, str(context.exception))

    def test_overlap_start_end(self):

        # Arrange
        rec_id = 'overlap'
        record_list = [{'name': 'Overlap', 'id': rec_id, 'start_before': '6 Jun 2040', 'end_before': '7 Jun 2040'}]
        start_min_ans = -math.inf
        start_max_ans = TimePoint(year=2040, month=6, day=6)
        end_min_ans = -math.inf  # Event cannot end before starting... but it could start anytime in the past
        end_max_ans = TimePoint(year=2040, month=6, day=7)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_min_ans)
        self.assertEqual(rec.start.max, start_max_ans)
        self.assertEqual(rec.end.min, end_min_ans)
        self.assertEqual(rec.end.max, end_max_ans)

    def test_fixed_start_bounded_end(self):

        # Arrange
        rec_id = 'bounded'
        record_list = [{'name': 'Bounded', 'id': rec_id, 'start': '6 Jun 2040', 'end_before': '7 Jun 2040'}]
        start_min_ans = TimePoint(year=2040, month=6, day=6)
        start_max_ans = start_min_ans  # fixed-point time reference
        end_min_ans = start_min_ans  # Can't end before start.min
        end_max_ans = TimePoint(year=2040, month=6, day=7)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_min_ans)
        self.assertEqual(rec.start.max, start_max_ans)
        self.assertEqual(rec.end.min, end_min_ans)
        self.assertEqual(rec.end.max, end_max_ans)

    def test_fixed_end_bounded_start(self):

        # Arrange
        rec_id = 'bounded'
        record_list = [{'name': 'Bounded', 'id': rec_id, 'start_after': '6 Jun 2040', 'end': '7 Jun 2040'}]
        start_min_ans = TimePoint(year=2040, month=6, day=6)
        end_ans = TimePoint(year=2040, month=6, day=7)
        start_max_ans = end_ans  # Can't start after it ends

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_min_ans)
        self.assertEqual(rec.start.max, start_max_ans)
        self.assertEqual(rec.end.min, end_ans)
        self.assertEqual(rec.end.max, end_ans)

    def test_unknown_record(self):

        # Arrange
        rec_id = 'broken_ref'
        record_list = [{'name': 'Broken Ref', 'id': rec_id, 'start_after': 'unknown_record'}]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        with self.assertRaises(UnknownEventRecordError) as context:
            records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertIn(rec_id, str(context.exception))

    def test_duration_simple(self):

        # Arrange
        rec_id = 'start_and_duration'
        record_list = [{'name': 'Start and Duration',
                        'id': rec_id,
                        'start': '6 Jun 2040',
                        'duration': '1y 1m 10d'}]
        start_ans = TimePoint(year=2040, month=6, day=6)
        end_ans = TimePoint(year=2041, month=7, day=16)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_ans)
        self.assertEqual(rec.start.max, start_ans)
        self.assertEqual(rec.end.min, end_ans)
        self.assertEqual(rec.end.max, end_ans)

    def test_duration_start_after(self):

        # Arrange
        rec_id = 'start_and_duration'
        record_list = [{'name': 'Start and Duration',
                        'id': rec_id,
                        'start_after': '6 Jun 2040',
                        'duration': '1y 1m 10d'}]
        start_ans = TimePoint(year=2040, month=6, day=6)
        end_ans = TimePoint(year=2041, month=7, day=16)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_ans)
        self.assertEqual(rec.start.max, math.inf)
        self.assertEqual(rec.end.min, end_ans)
        self.assertEqual(rec.end.max, math.inf)

    def test_duration_uncertain_start(self):

        # Specify an uncertain start and a duration. Ensure the end min/max are normalized correctly.
        # Arrange
        rec_id = 'uncertain_start_duration'
        record_list = [{'name': 'Uncertain Start with Duration',
                        'id': rec_id,
                        'start_after': '6 Jun 2040',
                        'start_before': '10 Jul 2040',
                        'duration': '1y 1m 10d'}]
        start_min_ans = TimePoint(year=2040, month=6, day=6)
        start_max_ans = TimePoint(year=2040, month=7, day=10)
        end_min_ans = TimePoint(year=2041, month=7, day=16)
        end_max_ans = TimePoint(year=2041, month=8, day=20)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_min_ans)
        self.assertEqual(rec.start.max, start_max_ans)
        self.assertEqual(rec.end.min, end_min_ans)
        self.assertEqual(rec.end.max, end_max_ans)

    def test_duration_uncertain_start_end(self):
        # Specify uncertain start and ends that are not strictly duration apart. Check normalization.
        # Arrange
        rec_id = 'duration_uncertain_start_end'
        record_list = [{'name': 'Uncertain Start and End with Duration',
                        'id': rec_id,
                        'start_after': '6 May 2040',  # Duration too short; this will shift right to match end_after.
                        'start_before': '10 Jul 2040',
                        'end_after': '16 Jul 2041',
                        'end_before': '20 Sep 2041',  # Duration too short; this will shift left to match start_before.
                        'duration': '1y 1m 10d'}]
        start_min_ans = TimePoint(year=2040, month=6, day=6)
        start_max_ans = TimePoint(year=2040, month=7, day=10)
        end_min_ans = TimePoint(year=2041, month=7, day=16)
        end_max_ans = TimePoint(year=2041, month=8, day=20)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_min_ans)
        self.assertEqual(rec.start.max, start_max_ans)
        self.assertEqual(rec.end.min, end_min_ans)
        self.assertEqual(rec.end.max, end_max_ans)

    def test_duration_uncertain_start_end_b(self):
        # Specify uncertain start and ends that are not strictly duration apart. Check normalization.
        # Arrange
        rec_id = 'duration_uncertain_start_end'
        record_list = [{'name': 'Uncertain Start and End with Duration',
                        'id': rec_id,
                        'start_after': '6 Jun 2040',
                        'start_before': '10 Aug 2040',  # Duration too long; this will shift left to match end_before.
                        'end_after': '16 Jun 2041',  # Duration too long; this will shift right to match start_after.
                        'end_before': '20 Aug 2041',
                        'duration': '1y 1m 10d'}]
        start_min_ans = TimePoint(year=2040, month=6, day=6)
        start_max_ans = TimePoint(year=2040, month=7, day=10)
        end_min_ans = TimePoint(year=2041, month=7, day=16)
        end_max_ans = TimePoint(year=2041, month=8, day=20)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_min_ans)
        self.assertEqual(rec.start.max, start_max_ans)
        self.assertEqual(rec.end.min, end_min_ans)
        self.assertEqual(rec.end.max, end_max_ans)

    def test_duration_inconsistent(self):
        # Specify duration, start, end, but no way to reconcile.
        # Arrange
        rec_id = 'duration_inconsistent'
        record_list = [{'name': 'Duration Inconsistent with Start/End',
                        'id': rec_id,
                        'start_after': '6 Jun 2040',
                        'start_before': '10 Aug 2040',
                        'end_after': '16 Jul 2041',
                        'end_before': '20 Aug 2041',
                        'duration': '1y 4m 10d'}]
        start_min_ans = TimePoint(year=2040, month=6, day=6)
        start_max_ans = TimePoint(year=2040, month=7, day=10)
        end_min_ans = TimePoint(year=2041, month=7, day=16)
        end_max_ans = TimePoint(year=2041, month=8, day=20)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        with self.assertRaises(InconsistentTimeReferenceError) as context:
            records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertIn(rec_id, str(context.exception))

    def test_offset(self):
        # Arrange
        rec_id = 'offset_time'
        record_list = [{'name': 'Resolved Time.',
                        'id': 'resolved_time',
                        'start': '6 Jun 2040',
                        'end': '16 Jul 2041'},
                       {'name': 'Offset Time',
                        'id': rec_id,
                        'start': 'resolved_time - 1y 1m 1d',
                        'end': 'resolved_time + 1y 1m 1d'}
                       ]
        start_min_ans = TimePoint(year=2039, month=5, day=5)
        start_max_ans = TimePoint(year=2039, month=5, day=5)
        end_min_ans = TimePoint(year=2042, month=8, day=17)
        end_max_ans = TimePoint(year=2042, month=8, day=17)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertIn(rec_id, records)
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_min_ans)
        self.assertEqual(rec.start.max, start_max_ans)
        self.assertEqual(rec.end.min, end_min_ans)
        self.assertEqual(rec.end.max, end_max_ans)

    def test_before_after_offset(self):
        # Arrange
        rec_id = 'offset_time'
        record_list = [{'name': 'Resolved Time.',
                        'id': 'resolved_time',
                        'start': '6 Jun 2040',
                        'end': '16 Jul 2041'},
                       {'name': 'Offset Time',
                        'id': rec_id,
                        'start_after': '^resolved_time - 1y 1m 1d',
                        'end_before': 'resolved_time$ + 1y 1m 1d'}
                       ]
        start_min_ans = TimePoint(year=2039, month=5, day=5)
        start_max_ans = TimePoint(year=2042, month=8, day=17)
        end_min_ans = TimePoint(year=2039, month=5, day=5)
        end_max_ans = TimePoint(year=2042, month=8, day=17)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertIn(rec_id, records)
        rec = records[rec_id]
        self.assertEqual(rec.start.min, start_min_ans)
        self.assertEqual(rec.start.max, start_max_ans)
        self.assertEqual(rec.end.min, end_min_ans)
        self.assertEqual(rec.end.max, end_max_ans)

    def test_sample_file(self):

        # Arrange
        filename = "test/data/test_sample.yaml"
        with open(filename) as file:
            loaded = yaml.safe_load(file)
        record_list = loaded["Records"]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = build_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), 10)
        for rid in records:
            self.assertNotEqual(records[rid].start.min, None)
            self.assertNotEqual(records[rid].start.max, None)
            self.assertNotEqual(records[rid].end.min, None)
            self.assertNotEqual(records[rid].end.max, None)
