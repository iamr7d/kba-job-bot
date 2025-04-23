import unittest
from utils.scoring import score

class TestScoring(unittest.TestCase):
    def test_score(self):
        self.assertGreaterEqual(score("Software Engineer", ["Engineer"]), 50)
        self.assertEqual(score("", ["Engineer"]), 0)
        self.assertEqual(score("Software Engineer", []), 0)
        self.assertEqual(score("Random", ["Unrelated"]), 40)

if __name__ == "__main__":
    unittest.main()
