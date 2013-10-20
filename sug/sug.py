"Command line interface for sug."

import sys
import os
# import re

from sug.getopt import Getopt, UnknownFlag

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
# - Run files through a script instead of a regexp
#
#   Stick every line of input to stdin of script, and read the result from the
#   stdout of it.  If did not return zero, do whatever is done when regexp does
#   not match.
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

def do_substitute(options, regexp_or_script, substitute, _file):
    print("chop", _file)

def check_exists_or_die(_file):
    "Check a _ile for existance and die if it doesn't."
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
    if any([options["F"], options["S"]]):
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
    sys.stdout.write("sug: usage: sug [-bopsSF] "
                     "(REGEXP|FILE) SUBSTITUTE FILES...\n")
    exit(2)

def main(argv):
    "Entry point to the program."
    opts = Getopt("sug", *argv,
                  b = (False, "back up files"),
                  F = (False, "read regexp from file"),
                  S = (False, "apply script instead of regexp"),
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

