
from typing import Dict
import unittest
from datetime import date
import math

from data_types import months
from algorithms import normalize_events, parse_record_list
from data_types import EventRecord


class TestNormalizeEvent(unittest.TestCase):

    def test_simple_case(self):

        # Arrange
        record_list = [{'name': 'Life', 'id': 'life', 'start': 'birth', 'end': 'death'},
                       {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                       {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'},
                       ]
        birth_date = date(day=17, month=months.index('aug'), year=1970)
        death_date = date(day=5, month=months.index('jun'), year=2040)

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
        birth_date = date(day=17, month=months.index('aug'), year=1970)
        death_date = date(day=5, month=months.index('jun'), year=2040)
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
        rec_end = date(day=5, month=months.index('jun'), year=2040)

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
