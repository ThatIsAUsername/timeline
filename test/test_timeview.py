
import unittest
from datetime import timedelta

from data_types import Timeline, TimePoint, Timeview, EventRecord


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

        early_date = TimePoint(year=1970, month=8, day=16)
        late_date = TimePoint(year=2040, month=6, day=6)
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
            {'name': 'wider than view',
             'start': 'July 1950',
             'end': 'Aug 2050',
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
        wide_dat = {'name': 'bef_aft', 'id': 'bef_aft', 'start': '10 Mar 1970', 'end': '11 Mar 2050'}
        wide_rec = EventRecord(wide_dat)

        view = Timeview(self.timeline)
        recs = list(self.timeline.get_records().values())
        recs.append(wide_rec)

        # Assert
        print('view range', view.min, view.max)
        for rr in recs:
            self.assertTrue(view.contains(rr), f"View contains {rr} ({rr.start.min}, {rr.end.max}) but claims not to.")

    def test_not_contains_record(self):

        # Arrange
        view = Timeview(self.timeline)  # Create Timeview from 17 Aug 1970 to 5 Jun 2040.
        rec_bef = {'name': 'before', 'id': 'before', 'start': '10 Mar 1970', 'end': '11 Mar 1970'}
        rec_aft = {'name': 'after', 'id': 'after', 'start': '10 Mar 2050', 'end': '11 Mar 2050'}
        recs = [EventRecord(rec_data) for rec_data in [rec_bef, rec_aft]]

        # Assert
        for rr in recs:
            self.assertFalse(view.contains(rr), f"View does not contain {rr} ({rr.start.min}, {rr.end.max}) but claims to.")

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

    def test_pan_right(self):

        # Arrange
        view = Timeview(self.timeline)
        min_date = date(year=1970, month=8, day=17)
        max_date = date(year=2040, month=6, day=5)

        delta = timedelta(days=10)

        min_ans = date(year=1970, month=8, day=27)
        max_ans = date(year=2040, month=6, day=15)

        # Act
        view.pan(delta)

        # Assert
        self.assertEqual(view.min, min_ans)
        self.assertEqual(view.max, max_ans)

    def test_pan_left(self):

        # Arrange
        view = Timeview(self.timeline)
        min_date = date(year=1970, month=8, day=17)
        max_date = date(year=2040, month=6, day=5)

        delta = timedelta(days=-4)

        min_ans = date(year=1970, month=8, day=13)
        max_ans = date(year=2040, month=6, day=1)

        # Act
        view.pan(delta)

        # Assert
        self.assertEqual(view.min, min_ans)
        self.assertEqual(view.max, max_ans)
