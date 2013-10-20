"Tests for sug/getopt.py"

# pylint: disable=R0904,C0103

from unittest import TestCase, TestLoader, TestSuite
from sug.getopt import Getopt

class GetoptTestCase(TestCase):
    "Base class for getopt tests."
    def __init__(self):
        super().__init__()
        self.g = None

    # The longest name I have ever used.
    # Run getopt_instance.parse() before passing in.
    def _test_getopt_with_expectancies(self, expected_options,
                                       expected_non_options):
        "Test Getopt class, after Getopt.parse has run."
        self.assertEqual(self.g.options(), expected_options)
        self.assertEqual(self.g.non_options(), expected_non_options)

class GetoptTestEmpty(GetoptTestCase):
    "Test call with no arguments."
    def setUp(self):
        self.g = Getopt("poppy")
        self.g.parse()

    def test_getopt(self):
        "Unit test for no arguments."
        expected_options = {}
        expected_non_options = ()
        self._test_getopt_with_expectancies(expected_options,
                                            expected_non_options)

class GetoptTestBasic(GetoptTestCase):
    "Test getopt with a small number of arguments."
    def setUp(self):
        self.g = Getopt("poppy", "-ahi,ho", "-qw", "ello", "-e",
                        a = (True, "asdf"),
                        q = (False, "asdf"),
                        w = (False, "asdf"))
        self.g.parse()

    def test_getopt(self):
        "Test getopt with a small number of arguments."
        expected_options = {"a": ["hi", "ho"], "q": True, "w": True}
        expected_non_options = ("ello", "-e")
        self._test_getopt_with_expectancies(expected_options,
                                            expected_non_options)

loader = TestLoader()
suite_empty = loader.loadTestsFromTestCase(GetoptTestEmpty)
suite_basic = loader.loadTestsFromTestCase(GetoptTestBasic)

alltests = TestSuite([suite_empty, suite_basic])
