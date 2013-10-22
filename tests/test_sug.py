# pylint: disable=R0904,C0103,C0111,C0301,W0613

from unittest import TestCase, TestLoader, TestSuite

from sug import sug

class Called(Exception):
    pass

class Passed(Exception):
    pass

def mock(*a):
    raise Called()

old_die = sug.die
sug.die = mock

IMPOSSIBLE_FILE = "/happy_new_year_eat_noodles_hopefullyTHIsfiledoesnotEXXIISSTTTTTTT.txt"

class TestCheckExistsOrDie(TestCase):
    def test_die_when_file_absent(self):
        "Must call die()."
        self.assertRaises(Called,
                          lambda: sug.check_exists_or_die(IMPOSSIBLE_FILE))
    def test_succeed_when_file_exists(self):
        "Must not call die()."
        try:
            sug.check_exists_or_die("/")
            raise Passed()
        except Passed as _:
            self.assertTrue(True)

loader = TestLoader()
suites = list()
suites.append(loader.loadTestsFromTestCase(TestCheckExistsOrDie))

alltests = TestSuite(suites)
