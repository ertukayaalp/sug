# pylint: disable=R0904,C0103,C0111,C0301,W0613,R0201,E0202,W0201

from unittest import TestCase

import subprocess
import re

ui_test_base_dir = "./ui_test_data/"
trash_dir = "./trash/"
sug = "scripts/sug_tester"

class StdioTest(TestCase):
    def make_subprocess(self, *args):
        self.__process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE)
        return self.__process
    def run_with_stdin(self, _bytes):
        self.__test_stdin = _bytes
        self.__stdout = self.__process.communicate(_bytes)
        self.__process.stdin.close()
        self.returncode = lambda: self.__process.returncode

    def returncode(self):
        raise ValueError("Write to stdin prior to this.")

    def assertSuccess(self):
        self.assertEqual(self.returncode(), 0)

    def assertStdoutIs(self, _bytes):
        self.assertEqual(_bytes, self.__stdout)

class TestsStdinInteraction(StdioTest):
    def setUp(self):
        self.test_str = b"Who guards the guards?"
        self.test_str2 = b"Gering-ding ding-ding ding-ding dinge-ring"

    # Substitute stuff with nothing.  Or basically delete matches.
    def test_basic_remove(self):
        self.make_subprocess(sug, "a")
        self.run_with_stdin(self.test_str)
        self.assertSuccess()
        u = "UTF-8"
        x = (re.sub(r"a", "",
                self.test_str.decode(encoding=u)).encode(encoding=u), None)
        self.assertStdoutIs(x)

    def test_basic_replace(self):
        self.make_subprocess(sug, "a", "b")
        self.run_with_stdin(self.test_str)
        self.assertSuccess()
        u = "UTF-8"
        x = (re.sub(r"a", "b",
                self.test_str.decode(encoding=u)).encode(encoding=u), None)
        self.assertStdoutIs(x)

    # What does the fox test?
    def test_basic_replace2(self):
        self.make_subprocess(sug, r"(Ger|d)ing-ding", "hattee")
        self.run_with_stdin(self.test_str2)
        self.assertSuccess()
        x = (b"hattee hattee hattee dinge-ring", None)
        self.assertStdoutIs(x)
