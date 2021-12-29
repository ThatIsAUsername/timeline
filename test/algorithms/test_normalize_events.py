
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
        self.assertEqual(records['death'].start.min, death_date)
        self.assertEqual(records['death'].start.max, death_date)
