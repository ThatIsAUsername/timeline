
import unittest
from datetime import date

from data_types import Timeline


class TestTimeline(unittest.TestCase):

    def test_load(self):

        # Arrange
        tl = Timeline()

        # Act
        tl.load("test/data/test_sample.yaml")

        # Assert
        self.assertEqual(len(tl.get_records()), 10)
        # for rec in tl.get_records().items():
        #     print(rec)

    def test_load_file(self):

        # Arrange
        min_ans = date(year=1900, month=1, day=1)
        max_ans = date(year=1975, month=6, day=29)

        # Act
        tl = Timeline()
        tl.load("test/data/test_sample.yaml")

        # Assert
        self.assertEqual(tl.min, min_ans)
        self.assertEqual(tl.max, max_ans)
