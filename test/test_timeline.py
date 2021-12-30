
import unittest

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
