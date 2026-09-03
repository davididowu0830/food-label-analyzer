"""
tests/test_food_log_manager.py
Owner: Usman Gaji

Uses a temporary file so tests never touch the real food_log.json, and
clean up after themselves regardless of pass/fail.
"""

import unittest
import os
import tempfile

from storage.food_log_manager import FoodLogManager
from exceptions import FoodLogError


class TestFoodLogManagerJSON(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)  # start with a file that doesn't exist yet
        self.manager = FoodLogManager(filepath=self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_load_log_when_file_missing_returns_empty_list(self):
        self.assertEqual(self.manager.load_log(), [])

    def test_save_and_load_entry(self):
        self.manager.save_entry({"barcode": "123", "name": "Test Product"})
        log = self.manager.load_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["name"], "Test Product")

    def test_multiple_entries_append(self):
        self.manager.save_entry({"barcode": "1", "name": "A"})
        self.manager.save_entry({"barcode": "2", "name": "B"})
        log = self.manager.load_log()
        self.assertEqual(len(log), 2)

    def test_corrupted_json_raises_food_log_error(self):
        with open(self.path, "w") as f:
            f.write("{ this is not valid json ]")
        with self.assertRaises(FoodLogError):
            self.manager.load_log()


class TestFoodLogManagerCSV(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        os.remove(self.path)
        self.manager = FoodLogManager(filepath=self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_save_and_load_csv_entry(self):
        entry = {
            "barcode": "999",
            "name": "CSV Product",
            "nutrients": {"sugars": 10, "salt": 1, "fat": 2, "energy_kcal": 100},
            "allergens": ["milk"],
        }
        self.manager.save_entry(entry)
        log = self.manager.load_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["name"], "CSV Product")
        self.assertEqual(log[0]["allergens"], "milk")


if __name__ == "__main__":
    unittest.main()
