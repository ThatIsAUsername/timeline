import math
import unittest
from datetime import date

from data_types import Timeline, Timeview, TimeReference, EventRecord


class TestTimeview(unittest.TestCase):

    def setUp(self):
        self.record_list =\
            [
                {'name': 'Life', 'id': 'life', 'start': 'birth', 'end': 'death'},
                {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'}
            ]
        self.timeline = Timeline()
        self.timeline.load_from_record_list(self.record_list)

    def test_buffer(self):

        # Arrange
        # Act
        view = Timeview(self.timeline)

        # Assert
        # Timeview should frame the min/max timeline dates by default.
        self.assertEqual(view.min, self.timeline.min)
        self.assertEqual(view.max, self.timeline.max)

    def test_contains(self):

        # Arrange
        # Act
        view = Timeview(self.timeline)

        # Assert
        for rr in self.timeline.get_records().values():
            self.assertTrue(view.contains(rr.start.min))

        early_date = date(year=1970, month=8, day=16)
        late_date = date(year=2040, month=6, day=6)
        for dd in [early_date, late_date]:
            self.assertFalse(view.contains(dd))

    def test_contains_reference(self):

        # Arrange

        # The timeline goes from 17 Aug 1970 to 5 Jun 2040.
        # The view contains the whole span by default, so we'll test against that.
        # Generate some new records that fall inside and outside that range.
        more_records = [
            {'name': 'in fixed point',
             'start': '4 Apr 2020',
             },
            {'name': 'in fixed range',
             'start': '1970',
             },
            {'name': 'in half infinity',
             'start_after': 'June 2000',
             },
            {'name': 'in half -infinity',
             'start_before': 'Sep 1970',
             },
            {'name': 'in unbounded'
             },

            {'name': 'out fixed point',
             'start': '4 June 1970',
             },
            {'name': 'out fixed range',
             'start': 'July 2040',
             },
            {'name': 'out half infinity',
             'start_after': 'July 2040',
             },
            {'name': 'out half -infinity',
             'start_before': 'July 1970',
             },
            ]
        tl2 = Timeline()
        tl2.load_from_record_list(more_records)
        contains_true = [event.start for event in tl2.get_records().values() if event.name.startswith('in')]
        contains_false = [event.start for event in tl2.get_records().values() if event.name.startswith('out')]

        # Act
        view = Timeview(self.timeline)

        # Assert
        for tr in contains_true:
            self.assertTrue(view.contains(tr))
        for tr in contains_false:
            self.assertFalse(view.contains(tr))

        early_date = date(year=1970, month=8, day=16)
        late_date = date(year=2040, month=6, day=6)
        for dd in [early_date, late_date]:
            self.assertFalse(view.contains(dd))

    def test_contains_record(self):

        # Arrange

        # Act
        view = Timeview(self.timeline)

        # Assert
        for rr in self.timeline.get_records().values():
            self.assertTrue(view.contains(rr.start.min))

        early_date = date(year=1970, month=8, day=16)
        late_date = date(year=2040, month=6, day=6)
        for dd in [early_date, late_date]:
            self.assertFalse(view.contains(dd))

    def test_zoom_in_min(self):
        # Zooming in on a point should not expand the view, and should not reduce
        # the view to exclude the zoomed-upon point.
        # Arrange
        view = Timeview(self.timeline)
        min_date = date(year=1970, month=8, day=17)
        max_date = date(year=2040, month=6, day=5)

        # Act
        view.zoom_in(min_date)

        # Assert
        self.assertTrue(view.contains(min_date), "Early date should still be in view")
        self.assertLess(view.max, max_date, "Late date should have shifted left")

    def test_zoom_in_max(self):

        # Arrange
        view = Timeview(self.timeline)
        min_date = date(year=1970, month=8, day=17)
        max_date = date(year=2040, month=6, day=5)

        # Act
        view.zoom_in(max_date)

        # Assert
        self.assertGreater(view.min, min_date, "Early date should have shifted right")
        self.assertTrue(view.contains(max_date), "Late date should still be in view")

    def test_zoom_in_center(self):

        # Arrange
        view = Timeview(self.timeline)
        min_date = date(year=1970, month=8, day=17)
        mid_date = date(year=2005, month=5, day=7)
        max_date = date(year=2040, month=6, day=5)

        # Act
        view.zoom_in(mid_date)

        # Assert
        self.assertGreater(view.min, min_date, "Early date should have shifted right")
        self.assertLess(view.max, max_date, "Late date should have shifted left")

    def test_zoom_out_min(self):

        # Arrange
        view = Timeview(self.timeline)
        min_date = date(year=1970, month=8, day=17)
        max_date = date(year=2040, month=6, day=5)

        # Act
        view.zoom_out(min_date)

        # Assert
        self.assertTrue(view.contains(min_date), "Early date should still be in view")
        self.assertTrue(view.contains(max_date), "Late date should still be in view")

    def test_zoom_out_max(self):

        # Arrange
        view = Timeview(self.timeline)
        min_date = date(year=1970, month=8, day=17)
        max_date = date(year=2040, month=6, day=5)

        # Act
        view.zoom_out(max_date)

        # Assert
        self.assertTrue(view.contains(min_date), "Early date should still be in view")
        self.assertTrue(view.contains(max_date), "Late date should still be in view")

    def test_zoom_out_center(self):

        # Arrange
        view = Timeview(self.timeline)
        min_date = date(year=1970, month=8, day=17)
        mid_date = date(year=2005, month=5, day=7)
        max_date = date(year=2040, month=6, day=5)

        # Act
        view.zoom_out(mid_date)

        # Assert
        self.assertTrue(view.contains(min_date), "Early date should still be in view")
        self.assertTrue(view.contains(max_date), "Late date should still be in view")
