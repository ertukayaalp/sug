# Tests for sug/getopt.py

from unittest import TestCase, TestLoader, TestSuite
from sug.getopt import Getopt

class GetoptTestCase(TestCase):
    # The longest name I have ever used.
    # Run getopt_instance.parse() before passing in.
    def _test_getopt_with_expectancies(self, expected_options, expected_non_options):
        self.assertEqual(self.G.options(), expected_options)
        self.assertEqual(self.G.non_options(), expected_non_options)

class GetoptTestEmpty(GetoptTestCase):
    def setUp(self):
        self.G = Getopt("poppy")
        self.G.parse()

    def test_getopt(self):
        expected_options = {}
        expected_non_options = ()
        self._test_getopt_with_expectancies(expected_options, expected_non_options)

class GetoptTestBasic(GetoptTestCase):
    def setUp(self):
        self.G = Getopt("poppy", "-ahi,ho", "-qw", "ello", "-e",
                        a = (True, "asdf"),
                        q = (False, "asdf"),
                        w = (False, "asdf"))
        self.G.parse()

    def test_getopt(self):
        expected_options = {"a": ["hi", "ho"], "q": True, "w": True}
        expected_non_options = ("ello", "-e")
        self._test_getopt_with_expectancies(expected_options, expected_non_options)

loader = TestLoader()
suite_empty  = loader.loadTestsFromTestCase(GetoptTestEmpty)
suite_basic  = loader.loadTestsFromTestCase(GetoptTestBasic)

alltests = TestSuite([suite_empty, suite_basic])
