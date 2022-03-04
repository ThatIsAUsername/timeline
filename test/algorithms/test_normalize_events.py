
from typing import Dict
import unittest
import math
import yaml

from algorithms import normalize_events, parse_record_list
from data_types import EventRecord, TimePoint, InconsistentTimeReferenceError, UnknownEventRecordError
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
        death_date = TimePoint(day=5, month=months.index('Aun'), year=2040)

        # Act
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        normalize_events(records)

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
        birth_date = TimePoint(day=17, month=months.index('aug'), year=1970)
        death_date = TimePoint(day=5, month=months.index('jun'), year=2040)
        start_ans = -math.inf
        end_ans = math.inf

        # Act
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        normalize_events(records)

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
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        normalize_events(records)

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
        rec_end = TimePoint(day=5, month=months.index('jun'), year=2040)

        # Act
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        normalize_events(records)

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
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        with self.assertRaises(InconsistentTimeReferenceError) as context:
            normalize_events(records)

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
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        normalize_events(records)

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
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        normalize_events(records)

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
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        normalize_events(records)

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
        records: Dict[str, EventRecord] = parse_record_list(record_list)
        with self.assertRaises(UnknownEventRecordError) as context:
            normalize_events(records)

        # Assert
        self.assertIn(rec_id, str(context.exception))

    def test_sample_file(self):

        # Arrange
        filename = "test/data/test_sample.yaml"
        with open(filename) as file:
            loaded = yaml.safe_load(file)
        record_list = loaded["Records"]

        # Act
        records = parse_record_list(record_list)
        normalize_events(records)

        # Assert
        self.assertEqual(len(records), 10)
        for rid in records:
            self.assertNotEqual(records[rid].start.min, None)
            self.assertNotEqual(records[rid].start.max, None)
            self.assertNotEqual(records[rid].end.min, None)
            self.assertNotEqual(records[rid].end.max, None)
