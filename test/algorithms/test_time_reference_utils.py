
import unittest
from data_types.time_reference import is_year, is_offset, is_event_ref


class TestTimeReferenceUtilities(unittest.TestCase):

    def test_is_year(self):
        # Valid years
        self.assertTrue(is_year("2023"))
        self.assertTrue(is_year(["-500"]))
        self.assertTrue(is_year("+100"))

        # Invalid years
        self.assertFalse(is_year("March"))
        self.assertFalse(is_year(["5", "March", "2023"]))
        self.assertFalse(is_year("event_id"))

    def test_is_offset(self):
        # Valid offsets
        self.assertTrue(is_offset(["event_id", "+", "1y", "2m"]))
        self.assertTrue(is_offset(["event_id", "-", "3d"]))
        self.assertTrue(is_offset(["event_id", "+", "1y"]))

        # Invalid offsets
        self.assertFalse(is_offset(["+", "1y", "2m"]))
        self.assertFalse(is_offset(["-", "3d"]))
        self.assertFalse(is_offset(["2023"]))
        self.assertFalse(is_offset(["March", "2023"]))
        self.assertFalse(is_offset(["event_id"]))

    def test_is_event_ref(self):
        # Valid event references
        # self.assertTrue(is_event_ref(["event_id"]))
        # self.assertTrue(is_event_ref(["event_id", "+", "1y"]))
        # self.assertTrue(is_event_ref(["event_id", "-", "2m"]))
        # self.assertTrue(is_event_ref(["^event_id"]))
        # self.assertTrue(is_event_ref(["event_id$"]))
        self.assertTrue(is_event_ref(['^resolved_time', '-', '1y', '1m', '1d']))

        # Invalid event references
        # self.assertFalse(is_event_ref(["2023"]))
        # self.assertFalse(is_event_ref(["5", "March", "2023"]))
        # self.assertFalse(is_event_ref(["+", "1y", "2m"]))

    # def test_is_date_string(self):
    #     # Valid date strings
    #     self.assertTrue(is_date_string(["5", "March", "2023"]))
    #     self.assertTrue(is_date_string(["March", "2023"]))
    #     self.assertTrue(is_date_string(["2023"]))

    #     # Invalid date strings
    #     self.assertFalse(is_date_string(["event_id"]))
    #     self.assertFalse(is_date_string(["event_id", "+", "1y"]))
    #     self.assertFalse(is_date_string(["+", "1y", "2m"]))


if __name__ == "__main__":
    unittest.main()
