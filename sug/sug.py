"Command line interface for sug."

import sys
import os
import re
import tempfile
import errno
import difflib

from sug.getopt import Getopt, UnknownFlag

# pylint: disable=W0142,C0103

#                          How to substitute globally?

# The intent of this program is to *safely* and *accurately* apply regular
# expressions to files *line by line*.  It is similar to sed(1).

# I think sed(1) has wrong defaults:  Most of the time, I want to substitute
# globally.  Most of the time, I want extended regexp.  Most of the time, I
# just want to change the file in-place.  This program (called `sug') is a go
# at making a more favorable stream edtiting tool.

# The flow of the program is as follows:

# - find out which files to operate on.
# - compile the regexp
# - A: pick a file to work on, if no more files, terminate.
#   - B: pick the next line from the file, if EOF, goto C.
#     - Apply the regexp.
#     - Push the resulting line to a list in memory.
#     - goto b
#   - C: Write file in an atomic manner. Goto A.

# A good optimization would be to act on a per file basis, close and deallocate
# all memory used with that file after the operations are done on it.

# Yet another good optimization would be to not keep a line if no substitutions
# happened on it: Just record which lines to change in a file and the versions
# of the line with the regexp applied.  Yes, I'm thinking of a file with lots
# and lots of lines with no matches.

#                                Fuck the s///

# The s/<pattern>/<substitute>/<options> syntax does not work: It is
# unreadable.  Instead, get <pattern> and <substitute> as seperate arguments,
# and <options> as standard command line arguments.

#                                   Options

# - Substitute once per line
#
#   The default behavior is to replace every match.  If this option is set,
#   however, do what uncle sed(1) does and replace once per line.
#
# - Generate a patch
#
#   Instead of changing file(s), generate the diff of the files' actual state
#   and the state on them when regexps applied.  Do not change the actual
#   files, but provide an option to do so.  Patch shall be in the standard
#   unified format, because why shouldn't it?
#
# - Write changed files to stdout
#
#   Apply changes to files, but instead of actually modifying files, write them
#   to stdout.
#
# - Back up files
#
#   Back up files if any change happened to them.
#
# - Read regexp from file
#
#   Instead of getting the regexp from arguments, get them from files.

#                               The sug library

# Instead of being a monolithic application, sug shall comprise a script and a
# library that the script uses:  Script shall be the command line interface to
# the library.

def rename(src, dest):
    """
    Handle when renaming fails because dest is on a different device than the
    one src is on.

    param src: The file to rename
    param dest: The new name for the file.
    """
    try:
        os.rename(src, dest)
    except OSError as oe:
        if oe.errno == errno.EXDEV:
            with open(dest, "w") as dest_file:
                with open(src, "r") as src_file:
                    dest_file.write(src_file.read())
                    dest_file.flush()
                    os.fsync(dest_file.fileno())
        else:
            raise oe

def atomic_write(_file, data, backup = False):
    """
    Perform an atomic write.

    param file: Path to the destination file.
    param data: Data to write to file, an iterable of strings
    """
    # Take no risks.
    assert (type(_file) == str) and (type(data) == list)

    # If two files are not on the same file system, os.rename will fail to be
    # atomic. Thus create the temporary file in the same directory as the
    # processed file in order to play it safe.
    tmp_fd, tmp_path = tempfile.mkstemp(text = True, dir = os.getcwd())

    with open(tmp_path, "w") as tmp_file:
        for i in data:
            tmp_file.write(i)
        tmp_file.flush()
    # Make sure the data is written to the filesystem.
    os.fsync(tmp_fd)

    if backup and os.path.exists(_file):
        rename(_file, _file + "~sug")

    rename(tmp_path, _file)
    # The temporary file is ought to be deleted automagically, says the docs.
    os.close(tmp_fd)

def write_to_stdout(_iterable):
    "Perform an atomic write to stdout."
    sys.stdout.write("".join(_iterable))
    sys.stdout.flush()

def do_substitute(options, regexp, substitute, _file):
    "Execute substitution."
    r = regexp
    backup = True if options["b"] else False
    to_diff = list()
    processed_file = list()
    if options["F"]:
        with open(regexp) as regex_file:
            r = regex_file.read()
    _regexp = re.compile(r)
    with open(_file) as f:
        for i in f:
            if options["p"]:
                to_diff.append(i)
            p = re.sub(_regexp, substitute, i)
            processed_file.append(p)
    if options["s"]:
        write_to_stdout(processed_file)
    elif options["p"]:
        diff = difflib.unified_diff(to_diff, processed_file, _file, _file)
        write_to_stdout(diff)
    else:
        atomic_write(_file, processed_file, backup)

def check_exists_or_die(_file):
    "Check a file for existance and die if it doesn't exist."
    try:
        os.stat(_file)
    except FileNotFoundError:
        die("cannot stat file `{0}'".format(_file))

def start(options, regexp_or_script, substitute, files):
    "Start processig files."
    for _file in files:
        check_exists_or_die(_file)
        if not os.path.isfile(_file):
            die("cannot operate on directories")
    # If the regexp is from file or a script will be uset for substitution,
    # make sure that given file exits.
    if options["F"]:
        check_exists_or_die(regexp_or_script)
    for _file in files:
        do_substitute(options, regexp_or_script, substitute, _file)

def die(reason):
    """
    Exit immediately, because of an error.

    param error: an error message.
    """
    raise SystemExit("sug: fatal: {0}".format(reason))

def usage():
    "Print usage message and exit error."
    sys.stdout.write("sug: usage: sug [-bopsF] "
                     "(REGEXP|FILE) SUBSTITUTE FILES...\n")
    exit(2)

def main(argv):
    "Entry point to the program."
    opts = Getopt("sug", *argv,
                  b = (False, "back up files"),
                  F = (False, "read regexp from file"),
                  s = (False, "write changes to stdout"),
                  p = (False, "generate a patch from results, write to stdout"),
                  o = (False,
                       "substitute only the first occurence on every line"))
    try:
        opts.parse()
    except UnknownFlag:
        usage()

    options = opts.options()
    non_options = opts.non_options()

    if len(non_options) < 3:
        usage()

    start(options, non_options[0], non_options[1], non_options[2:])

if __name__ == "__main__":
    exit(main(sys.argv[1:]))

