import unittest
from src.scraper import Scraper
from src.urlbuilder import URLBuilder


class TestScraper(unittest.TestCase):
    def setUp(self):
        self.sample_url_builder = URLBuilder(item_query="test", city="test_city", distance=100)
        self.scraper = Scraper([self.sample_url_builder])

    def test_add_url(self):
        new_url_builder = URLBuilder(item_query="new_test", city="new_test_city", distance=50)
        self.scraper.add_url(new_url_builder)
        self.assertIn(new_url_builder, self.scraper.url_list)

    def test_generate_data_key(self):
        key = self.scraper._generate_data_key(self.sample_url_builder)
        self.assertEqual(key, "Test - Test_city")

    # Add more test methods for other functionalities


if __name__ == '__main__':
    unittest.main()
