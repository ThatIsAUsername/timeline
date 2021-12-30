
import unittest

import yaml
from data_types import TimeReference, EventRecord


class TestEventRecord(unittest.TestCase):

    def test_simple_construction(self):

        # Arrange
        record_data = {'name': 'Life', 'id': 'life', 'start_before': 'birth', 'end': 'death'}

        # Act
        er = EventRecord(record_data)

        # Assert
        self.assertEqual(er._data, record_data)
        self.assertEqual(er.name, 'Life')
        self.assertEqual(er.id, 'life')
        self.assertEqual(type(er.start), TimeReference)
        self.assertEqual(type(er.start.min), type(None))  # No absolute dates provided.
        self.assertEqual(type(er.start.max), type(None))  # No absolute dates provided.
        self.assertIn('birth', er.start._later_refs)
        self.assertEqual(type(er.end), TimeReference)
        self.assertIn('^death', er.end._older_refs)
        self.assertIn('death$', er.end._later_refs)
