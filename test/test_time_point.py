
import unittest

from datetime import timedelta
from data_types import TimePoint


class TestTimePoint(unittest.TestCase):

    def test_construct(self):

        # Arrange
        year = 1800
        month = 5
        day = 2

        # Act
        tp = TimePoint(year=year, month=month, day=day)

        # Assert
        self.assertEqual(tp.year, year)
        self.assertEqual(tp.month, month)
        self.assertEqual(tp.day, day)

    def test_compare(self):

        # Arrange
        year = 1800
        month = 5
        day = 2

        # Act
        tp = TimePoint(year=year, month=month, day=day)
        tp_same = TimePoint(year=year, month=month, day=day)
        tp_later = TimePoint(year=year, month=month, day=day+1)
        tp_sooner = TimePoint(year=year, month=month, day=day-1)

        # Assert
        self.assertEqual(tp, tp_same)

        self.assertLess(tp, tp_later)
        self.assertLessEqual(tp, tp_same)
        self.assertLessEqual(tp, tp_later)

        self.assertGreater(tp, tp_sooner)
        self.assertGreaterEqual(tp, tp_same)
        self.assertGreaterEqual(tp, tp_sooner)

    def test_construct_normalize(self):

        # Arrange
        y1, m1, d1 = 1800, 5, 35  # should roll to June 4
        y1a, m1a, d1a = 1800, 6, 4

        y2, m2, d2 = 1800, 6, 35  # should roll to July 5
        y2a, m2a, d2a = 1800, 7, 5

        y3, m3, d3 = 1800, 12, 35  # should roll to 4 Jan 1801
        y3a, m3a, d3a = 1801, 1, 4

        # Act
        tp1 = TimePoint(year=y1, month=m1, day=d1)
        tp1a = TimePoint(year=y1a, month=m1a, day=d1a)
        tp2 = TimePoint(year=y2, month=m2, day=d2)
        tp2a = TimePoint(year=y2a, month=m2a, day=d2a)
        tp3 = TimePoint(year=y3, month=m3, day=d3)
        tp3a = TimePoint(year=y3a, month=m3a, day=d3a)

        # Assert
        self.assertEqual(tp1, tp1a)
        self.assertEqual(tp2, tp2a)
        self.assertEqual(tp3, tp3a)

    def test_subtract(self):
        # Arrange
        y1, m1, d1 = 1800, 5, 2
        y2, m2, d2 = 1700, 5, 2
        y3, m3, d3 = 1800, 4, 2
        y4, m4, d4 = 1800, 5, 18
        tp1 = TimePoint(year=y1, month=m1, day=d1)
        tp2 = TimePoint(year=y2, month=m2, day=d2)
        tp3 = TimePoint(year=y3, month=m3, day=d3)
        tp4 = TimePoint(year=y4, month=m4, day=d4)

        # Act
        diff12 = tp1 - tp2  # Should be a timedelta of 100 years (> 36000 days)
        diff21 = tp2 - tp1  # Should be a negative timedelta in the same range.
        diff13 = tp1 - tp3  # A delta of 1 month (from April to March - 31 days)
        diff31 = tp3 - tp1  # A negative 31-day delta.
        diff14 = tp1 - tp4  # -16 days; in the same month.
        diff41 = tp4 - tp1  # 16 days

        # Assert
        self.assertEqual(type(diff12), timedelta)
        self.assertGreater(diff12.days, 36000)
        self.assertLess(diff21.days, -36000)
        self.assertEqual(diff13.days, 30)
        self.assertEqual(diff31.days, -30)
        self.assertEqual(diff14.days, -16)
        self.assertEqual(diff41.days, 16)

    def test_add(self):
        # Arrange
        y1, m1, d1 = 1800, 5, 2
        tp = TimePoint(year=y1, month=m1, day=d1)
        td1 = timedelta(days=20)
        ans1 = TimePoint(year=y1, month=m1, day=d1+20)
        td2 = timedelta(days=-30)
        ans2 = TimePoint(year=y1, month=m1-1, day=d1)

        # Act
        tp1 = tp + td1
        tp2 = tp + td2

        # Assert
        self.assertEqual(tp1, ans1)
        self.assertEqual(tp2, ans2)

    def test_ordinal(self):
        # Arrange
        y1, m1, d1 = 1, 1, 1
        tp = TimePoint(year=y1, month=m1, day=d1)
        ans1 = 1
        y2, m2, d2 = 0, 12, 31  # calendar treats year zero as 1 BC.
        tp2 = TimePoint(year=y2, month=m2, day=d2)
        ans2 = 0

        # Act
        ord1 = tp.ordinal()
        ord2 = tp2.ordinal()

        # Assert
        self.assertEqual(ord1, ans1)
        self.assertEqual(ord2, ans2)

    def test_from_ordinal(self):
        # Arrange
        y1, m1, d1 = 1900, 1, 21
        y2, m2, d2 = -559, 5, 9
        ans1 = TimePoint(year=y1, month=m1, day=d1)
        ans2 = TimePoint(year=y2, month=m2, day=d2)

        # Act
        tp1 = TimePoint.from_ordinal(ans1.ordinal())
        tp2 = TimePoint.from_ordinal(ans2.ordinal())

        # Assert
        self.assertEqual(tp1, ans1)
        self.assertEqual(tp2, ans2)
