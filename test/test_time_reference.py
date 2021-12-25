
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

