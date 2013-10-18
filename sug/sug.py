import sug.getopt
import sys
import re

#                          How to subsitute globally?

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

def main(argv):
    return 0

if __name__ == "__main__":
    exit(main(sys.argv))

