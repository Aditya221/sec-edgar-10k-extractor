import unittest
from edgar_extractor import extract_10k_mda

class TestEdgarExtractor(unittest.TestCase):
    
    def setUp(self):
        self.test_email = "test_suite_runner@example.com"

    def test_successful_extraction_apple(self):
        result = extract_10k_mda("apple.com", self.test_email)
        self.assertIsNotNone(result)
        self.assertEqual(result["company"], "APPLE INC")
        self.assertTrue(len(result["mda_excerpt"]) > 100)
        self.assertIn("https://www.sec.gov/Archives/edgar/data/", result["source_url"])

if __name__ == '__main__':
    unittest.main()