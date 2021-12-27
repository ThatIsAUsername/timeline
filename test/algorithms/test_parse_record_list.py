
import unittest
from algorithms import parse_record_list


class TestConvert(unittest.TestCase):

    def test_parse_record_list(self):

        # Arrange
        record_list = [{'name': 'Life', 'id': 'life', 'start_before': 'birth', 'end': 'death'},
                       {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                       {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'},
                       ]

        # Act
        records = parse_record_list(record_list)

        # Assert
        self.assertEqual(len(records), len(record_list))
        for entry in record_list:
            self.assertIn(entry['id'], records)

    def test_generate_ids(self):

        # Arrange
        record_list = [{'name': 'Name Duplicate'},
                       {'name': 'Name Duplicate'},
                       {'name': 'Name Duplicate'},
                       ]

        # Act
        records = parse_record_list(record_list)

        # Assert
        print('records:', records)
        self.assertEqual(len(records), len(record_list))
        self.assertIn('nd', records)
        self.assertIn('nd2', records)
        self.assertIn('nd3', records)
