
import unittest
from datetime import date

from data_types import Timeline, Timeview, EventRecord


class TestTimeview(unittest.TestCase):

    def setUp(self):
        self.record_list =\
            [
                {'name': 'Life', 'id': 'life', 'start': 'birth', 'end': 'death'},
                {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'}
            ]

    def test_buffer(self):

        # Arrange
        tl = Timeline()
        tl.load_from_record_list(self.record_list)

        # Act
        view = Timeview(tl)

        # Assert
        # Timeview should frame the min/max timeline dates by default.
        self.assertEqual(view.min, tl.min)
        self.assertEqual(view.max, tl.max)

    def test_contains(self):

        # Arrange
        tl = Timeline()
        tl.load_from_record_list(self.record_list)

        # Act
        view = Timeview(tl)

        # Assert
        for rr in tl.get_records().values():
            self.assertTrue(view.contains(rr.start.min))

        early_date = date(year=1970, month=8, day=16)
        late_date = date(year=2040, month=6, day=6)
        for dd in [early_date, late_date]:
            self.assertFalse(view.contains(dd))
