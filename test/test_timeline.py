
import unittest
from datetime import date

from data_types import Timeline


class TestTimeline(unittest.TestCase):

    def test_load_from_file(self):

        # Arrange
        tl = Timeline()
        min_ans = date(year=1900, month=1, day=1)
        max_ans = date(year=1975, month=6, day=29)

        # Act
        tl.load_from_file("test/data/test_sample.yaml")

        # Assert
        self.assertEqual(len(tl.get_records()), 10)
        self.assertEqual(tl.min, min_ans)
        self.assertEqual(tl.max, max_ans)

    def test_load_from_list(self):

        # Arrange
        record_list = [{'name': 'Life', 'id': 'life', 'start': 'birth', 'end': 'death'},
                       {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                       {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'},
                       ]
        min_ans = date(year=1970, month=8, day=17)
        max_ans = date(year=2040, month=6, day=5)

        # Act
        tl = Timeline()
        tl.load_from_record_list(record_list)

        # Assert
        self.assertEqual(len(tl.get_records()), 3)
        self.assertEqual(tl.min, min_ans)
        self.assertEqual(tl.max, max_ans)
