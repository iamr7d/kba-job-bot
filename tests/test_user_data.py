import unittest
from utils.user_data import load_user_data, save_user_data
import os

class TestUserData(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_user_data.json"
        self.sample_data = {"123": {"gemini_jobs": ["Engineer"]}}
        # Patch the module variable for test
        global USERDATA_FILE
        USERDATA_FILE = self.test_file

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_save_and_load(self):
        save_user_data(self.sample_data)
        loaded = load_user_data()
        self.assertEqual(loaded, self.sample_data)

if __name__ == "__main__":
    unittest.main()
