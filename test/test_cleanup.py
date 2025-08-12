import unittest
from src.dita.cleanup import NAME, VERSION, DESCRIPTION

class TestDitaCleanup(unittest.TestCase):
    def test_name_exposed(self):
        self.assertIsInstance(NAME, str)
        self.assertNotEqual(NAME, '')

    def test_version_exposed(self):
        self.assertIsInstance(VERSION, str)
        self.assertNotEqual(VERSION, '')

    def test_description_exposed(self):
        self.assertIsInstance(DESCRIPTION, str)
        self.assertNotEqual(DESCRIPTION, '')
