import unittest
from main import Luxmed
import config
import re


class TestScrapper(unittest.TestCase):

    def test_get_main_page(self):
        luxmed = Luxmed(config.email, config.password)
        response = luxmed.getMainPage()
        self.assertEqual(response.status_code, 200)
        match = re.search('Zaloguj\s+się', response.text)
        self.assertIsNotNone(match)


if __name__ == '__main__':
    unittest.main()
