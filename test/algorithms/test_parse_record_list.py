
from typing import Dict
import unittest
from data_types import EventRecord, EventData
from algorithms import parse_record_list


class TestConvert(unittest.TestCase):

    def test_parse_record_list(self):

        # Arrange
        record_list = [{'name': 'Life', 'id': 'life', 'start_before': 'birth', 'end': 'death'},
                       {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                       {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = parse_record_list(evt_datas)

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
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = parse_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), len(record_list))
        self.assertIn('nd', records)
        self.assertIn('nd2', records)
        self.assertIn('nd3', records)

    def test_duplicate_ids(self):

        # Arrange - these two records should be merged
        record_list = [{'name': 'Name Duplicate', 'id': 'nd', 'end': '1000'},
                       {'name': 'Name Duplicate', 'id': 'nd', 'start': '0'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = parse_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), 1)
        self.assertIn('nd', records)

    def test_duplicate_ids_implicit(self):

        # Arrange - these two should not be merged since the id's don't match explicitly.
        record_list = [{'name': 'Name Duplicate', 'id': 'nd'},
                       {'name': 'Name Duplicate'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = parse_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), len(record_list))
        self.assertIn('nd', records)
        self.assertIn('nd2', records)

    def test_duplicate_ids_implicit_reverse(self):

        # Arrange - these two should not be merged since the id's don't match explicitly.
        record_list = [{'name': 'Name Duplicate'},
                       {'name': 'Name Duplicate', 'id': 'nd'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventRecord] = parse_record_list(evt_datas)

        # Assert
        self.assertEqual(len(records), len(record_list))
        self.assertIn('nd', records)
        self.assertIn('nd2', records)
