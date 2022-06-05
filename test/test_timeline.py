
import unittest

from data_types import Timeline, TimePoint, EventData


class TestTimeline(unittest.TestCase):

    def test_load_records(self):

        # Arrange
        tl = Timeline()
        min_ans = TimePoint(year=1900, month=1, day=1)
        max_ans = TimePoint(year=1975, month=6, day=29)

        # Act
        tl.load_records("test/data/test_sample.yaml")

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
        min_ans = TimePoint(year=1970, month=8, day=17)
        max_ans = TimePoint(year=2040, month=6, day=5)

        # Act
        tl = Timeline()
        evt_datas = [EventData.parse(rec) for rec in record_list]
        tl.init_from_record_list(evt_datas)

        # Assert
        self.assertEqual(len(tl.get_records()), 3)
        self.assertEqual(tl.min, min_ans)
        self.assertEqual(tl.max, max_ans)
