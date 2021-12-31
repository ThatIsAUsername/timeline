
import unittest
from datetime import date

from data_types import Timeline, Timeview


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
        self.assertLess(view.min, tl.min)
        self.assertGreater(view.max, tl.max)
