
import unittest

from datetime import date
from data_types import TimeReference, months


class TestTimeReference(unittest.TestCase):

    def test_absolute(self):

        # Arrange
        date_str = "01 Jan 2021"

        date_ans = date(day=1, month=months.index('jan'), year=2021)
        date_ans_ord = date_ans.toordinal()

        # Act
        tr = TimeReference(absolute=date_str)

        # Assert
        # Since we initialized the TimeReference with an absolute time,
        # the min and max possible reference values should be the same.
        self.assertEqual(date_ans_ord, tr.min.toordinal())
        self.assertEqual(date_ans_ord, tr.max.toordinal())

    def test_absolute_no_day(self):

        # Arrange
        date_str = "Jan 2021"

        # The provided date includes no day, so it should assume a min and max of the month's bounds.
        ans_beg = date(day=1, month=months.index('jan'), year=2021)
        ans_beg_ord = ans_beg.toordinal()
        ans_end = date(day=31, month=months.index('jan'), year=2021)
        ans_end_ord = ans_end.toordinal()

        # Act
        tr = TimeReference(absolute=date_str)

        # Assert
        self.assertEqual(ans_beg_ord, tr.min.toordinal())
        self.assertEqual(ans_end_ord, tr.max.toordinal())

    def test_absolute_no_month(self):

        # Arrange
        date_str = "2021"

        # The provided date includes no day, so it should assume a min and max of the month's bounds.
        ans_beg = date(day=1, month=months.index('jan'), year=2021)
        ans_beg_ord = ans_beg.toordinal()
        ans_end = date(day=31, month=months.index('dec'), year=2021)
        ans_end_ord = ans_end.toordinal()

        # Act
        tr = TimeReference(absolute=date_str)

        # Assert
        self.assertEqual(ans_beg_ord, tr.min.toordinal())
        self.assertEqual(ans_end_ord, tr.max.toordinal())

    def test_absolute_reference(self):

        # Arrange
        # By using a reference to the other event, we are saying that this
        # TimeRef occurred sometime during the referenced event.
        event_ref = "other_event"
        ans_older = "^other_event"  # The other event must have begun before this TimeRef begun.
        ans_later = "other_event$"  # The other event must have ended after this TimeRef ended.

        # Act
        tr = TimeReference(absolute=event_ref)

        # Assert
        self.assertEqual(tr.min, None)  # Since we just provided a reference, the min/max is not yet known.
        self.assertEqual(tr.max, None)  # Since we just provided a reference, the min/max is not yet known.
        self.assertIn(ans_older, tr._older_refs)
        self.assertIn(ans_later, tr._later_refs)

    def test_absolute_reference_pinned(self):

        # Arrange
        # By using a reference to the other event's beginning, we say that
        # this ref begins and ends at that specific point in time.
        event_ref = "^other_event"
        ans_older = "^other_event"  # The other event must have begun before this TimeRef begun.
        ans_later = "^other_event"  # This TimeRef must end when the other end begins as well.

        # Act
        tr = TimeReference(absolute=event_ref)

        # Assert
        self.assertIn(ans_older, tr._older_refs)
        self.assertIn(ans_later, tr._later_refs)

    def test_relative_lists_dates(self):

        # Arrange
        older_str = "01 Jan 2021"  # This date is known to be before this TimeReference.
        later_str = "05 Mar 2022"  # This one must be after

        # This time reference should thus begin at after_str and end at before_str.
        ans_beg = date(day=1, month=months.index('jan'), year=2021)
        ans_beg_ord = ans_beg.toordinal()
        ans_end = date(day=5, month=months.index('mar'), year=2022)
        ans_end_ord = ans_end.toordinal()

        # Act
        tr = TimeReference(older=older_str, later=later_str)

        # Assert
        # Ensure the dates were properly parsed into the older/newer ref lists.
        self.assertEqual(type(tr._older_refs), list)
        self.assertEqual(type(tr._later_refs), list)
        self.assertEqual(len(tr._older_refs), 1)
        self.assertEqual(len(tr._later_refs), 1)
        self.assertEqual(ans_beg_ord, tr._older_refs[0].toordinal())
        self.assertEqual(ans_end_ord, tr._later_refs[0].toordinal())

    def test_relative_lists_refs(self):

        # Arrange
        older_str = "earlier_event"  # This date is known to be before this TimeReference.
        later_str = "later_event"  # This one must be after

        # Act
        tr = TimeReference(older=older_str, later=later_str)

        # Assert
        # Ensure the dates were properly parsed into the older/newer ref lists.
        self.assertEqual(type(tr._older_refs), list)
        self.assertEqual(type(tr._later_refs), list)
        self.assertEqual(len(tr._older_refs), 1)
        self.assertEqual(len(tr._later_refs), 1)
        self.assertIn(older_str, tr._older_refs)
        self.assertIn(later_str, tr._later_refs)
