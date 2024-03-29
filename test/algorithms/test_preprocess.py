
from typing import List, Dict
import unittest
from data_types import EventRecord, EventData
from algorithms import preprocess_event_data


class TestAssignIds(unittest.TestCase):

    def test_basic(self):

        # Arrange
        record_list = [{'name': 'Life', 'id': 'life', 'start_before': 'birth', 'end': 'death'},
                       {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                       {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventData] = preprocess_event_data(evt_datas)
        rec_ids: List[str] = list(records.keys())

        # Assert
        self.assertEqual(len(records), len(record_list))
        for entry in record_list:
            self.assertIn(entry['id'], rec_ids)

    def test_generate_ids(self):

        # Arrange
        record_list = [{'name': 'Name Duplicate'},
                       {'name': 'Name Duplicate'},
                       {'name': 'Name Duplicate'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventData] = preprocess_event_data(evt_datas)
        rec_ids: List[str] = list(records.keys())

        # Assert
        self.assertEqual(len(records), len(record_list))
        self.assertIn('nd', rec_ids)
        self.assertIn('nd2', rec_ids)
        self.assertIn('nd3', rec_ids)

    def test_duplicate_ids(self):

        # Arrange - these two records should be merged
        record_list = [{'name': 'Name Duplicate', 'id': 'nd', 'end': '1000'},
                       {'name': 'Name Duplicate', 'id': 'nd', 'start': '0'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventData] = preprocess_event_data(evt_datas)
        rec_ids: List[str] = list(records.keys())

        # Assert
        self.assertEqual(len(records), 1)
        self.assertIn('nd', rec_ids)

    def test_duplicate_ids_multipass(self):

        # Arrange - these two records should be merged, but have insufficient data
        # to fix on the timeline. Make sure we handle this case correctly on the second pass too.
        record_list = [{'name': 'Name Duplicate', 'id': 'nd'},
                       {'name': 'Name Duplicate', 'id': 'nd'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventData] = preprocess_event_data(evt_datas)
        rec_ids: List[str] = list(records.keys())

        # Assert
        self.assertEqual(len(records), 1)
        self.assertIn('nd', rec_ids)

    def test_duplicate_ids_implicit(self):

        # Arrange - these two should not be merged since the id's don't match explicitly.
        record_list = [{'name': 'Name Duplicate', 'id': 'nd'},
                       {'name': 'Name Duplicate'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventData] = preprocess_event_data(evt_datas)
        rec_ids: List[str] = list(records.keys())

        # Assert
        self.assertEqual(len(records), len(record_list))
        self.assertIn('nd', rec_ids)
        self.assertIn('nd2', rec_ids)

    def test_duplicate_ids_implicit_reverse(self):

        # Arrange - these two should not be merged since the id's don't match explicitly.
        record_list = [{'name': 'Name Duplicate'},
                       {'name': 'Name Duplicate', 'id': 'nd'},
                       ]

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventData] = preprocess_event_data(evt_datas)
        rec_ids: List[str] = list(records.keys())

        # Assert
        self.assertEqual(len(records), len(record_list))
        self.assertIn('nd', rec_ids)
        self.assertIn('nd2', rec_ids)

    def test_merge(self):

        # Arrange
        record_list = [{'name': 'Life', 'id': 'life', 'start_before': 'birth'},
                       {'name': 'Birth', 'id': 'birth', 'start': '17 Aug 1970', 'end': '17 Aug 1970'},
                       {'name': 'Death', 'id': 'death', 'start': '5 Jun 2040', 'end': '5 Jun 2040'},
                       {'name': 'Life', 'id': 'life', 'end': 'death'},  # Life definition spread across multiple entries.
                       {'name': 'Life', 'id': 'life', 'end_after': 'birth'},  # Life definition spread across multiple entries.
                       ]
        ids = set([item['id'] for item in record_list])  # Convert to a set of ids to get the true number of entries.
        true_len = len(ids)

        # Act
        evt_datas = [EventData.parse(rec) for rec in record_list]
        records: Dict[str, EventData] = preprocess_event_data(evt_datas)
        rec_ids: List[str] = list(records.keys())

        # Assert
        self.assertEqual(len(records), true_len)
        for entry in record_list:
            self.assertIn(entry['id'], rec_ids)

        life_entry = records['life']
        self.assertTrue(life_entry.start_before)
        self.assertTrue(life_entry.end_after)
        self.assertTrue(life_entry.end)
