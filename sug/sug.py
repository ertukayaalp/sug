"Command line interface for sug."

import difflib
import errno
import os
import re
import select
import sys
import tempfile

from sug.getopt import Getopt, UnknownFlag

ANY_STDIN = select.select([sys.stdin], [], [], 0)[0]

USAGE_STRING = "sug: usage: sug [-bhopsF] (REGEXP|FILE) SUBSTITUTE FILES...\n"

HELP_STRING = """\
{usage}
Options:
    -b back up files
    -h show this help text
    -o substitute only the first occurence on every line
    -p generate a patch from results, then write to stdout
    -s write changes to stdout
    -F read regexp from file

Arguments:
    REGEXP: the expression to apply to input.
    FILE: if -F flag is set, the contents of this file will be used as the
          regexp
    FILES: The files ti operate on.  sug expects to operate on regular files.

""".format(usage=USAGE_STRING)

def help():
    sys.stdout.write(HELP_STRING)
    exit(0)

def oserror_die(oe):
    """
    Report an OSError.

    oe: an OSError instance.
    """
    die("{0}: `{1}'".format(oe.strerror, oe.filename), oe.errno)

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
            try:
                dest_file = open(dest, "w")
                src_file = open(src, "r")
                dest_file.write(src_file.read())
                dest_file.flush()
                os.fsync(dest_file.fileno())
            except OSError as oe1:
                oserror_die(oe1)
        else:
            oserror_die(oe)

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
    tempdir = os.path.dirname(os.path.realpath(_file))
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(text = True, dir = tempdir)
    except OSError as oe:
        oserror_die(oe)

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
    """
    Write the iterable to stdout, joining all the contents.

    param _iterable: Any iterable of strings.
    """
    sys.stdout.write("".join(_iterable))
    sys.stdout.flush()

def do_substitute(options, regexp_or_script, substitute, _file, stdin = False):
    """
    Execute the subtitution.

    param options: A parsed Getopt object.
    param regexp: The regexp (or a file containing the regexp) to apply.
    param substitute: The expression to substitute with matches.
    param _file: A list of files to operate on.
    param stdin: A boolean value, whether to operate on stdin or not.
    """
    regexp = regexp_or_script
    backup = True if options["b"] else False
    to_diff = list()
    processed_file = list()
    if options["F"]:
        with open(regexp_or_script) as regexp_file:
            regexp = regexp_file.read()
    try:
        _regexp = re.compile(regexp)
    except re.error:
        die("invalid regexp", 2)
    _file_obj = sys.stdin
    if not stdin:
        _file_obj = open(_file, "r")
    for i in _file_obj:
        if options["p"]:
            to_diff.append(i)
        # Now actually apply regexp.
        count = 1 if options["o"] else 0
        try:
            processed_line = re.sub(_regexp, substitute, i, count = count)
        except re.error:
            die("invalid backreference in substitute expression", 2)
        processed_file.append(processed_line)
    if options["s"]:
        write_to_stdout(processed_file)
    elif options["p"]:
        diff = difflib.unified_diff(to_diff, processed_file,
                                    _file or "<stdin>",
                                    _file or "<stdin>")
        write_to_stdout(diff)
    elif not stdin:
        atomic_write(_file, processed_file, backup)
    else:
        write_to_stdout(processed_file)

def check_exists_or_die(_file):
    """
    Check a file for existance and die if it doesn't exist.

    param _file: A path.
    """
    try:
        os.stat(_file)
    except FileNotFoundError:
        die("cannot stat file `{0}'".format(_file), 3)

def start(options, regexp_or_script, substitute, files):
    """
    Start processig files.

    param options: A Getopt instance.
    param regexp_or_script: Either a regexp or path to a file containing a
    regexp; contents are fed to re.compile.
    substitute: Expression to substitute matches.
    files: A list of file paths to operate on.
    """
    # If anything piped, operate on that too.
    if ANY_STDIN:
        do_substitute(options, regexp_or_script, substitute, None, True)
    for _file in files:
        check_exists_or_die(_file)
        if not os.path.isfile(_file):
            die("cannot operate on non-regular files")
    # If the regexp is from file or a script will be use for substitution,
    # make sure that given file exits.
    if options["F"]:
        check_exists_or_die(regexp_or_script)
    for _file in files:
        do_substitute(options, regexp_or_script, substitute, _file)

def die(reason, exit_code = 1):
    """
    Exit immediately, because of an error.

    param error: an error message.
    """
    sys.stdout.write("sug: fatal: {0}\n".format(reason))
    exit(exit_code)

def usage():
    "Print usage message and exit error."
    sys.stdout.write(USAGE_STRING)
    exit(4)

def main(argv):
    """
    Entry point to the program.

    param argv: A list of arguments to the program.
    """
    opts = Getopt("sug", *argv,
                  b = (False, "back up files"),
                  F = (False, "read regexp from file"),
                  s = (False, "write changes to stdout"),
                  p = (False, "generate a patch from results, write to stdout"),
                  o = (False,
                       "substitute only the first occurence on every line"),
                  h = (False, 'show this help'))
    try:
        opts.parse()
    except UnknownFlag:
        usage()

    options = opts.options()
    non_options = opts.non_options()
    n = len(non_options)

    if options['h']:
        help()
    # Delete stuff from stdin.
    if n == 1 and ANY_STDIN:
        start(options, non_options[0], r"", [])
    # Substitute stuff from stdin.
    elif n == 2 and ANY_STDIN:
        start(options, non_options[0], non_options[1], [])
    # Delete stuff from file.
    elif n == 2 and not ANY_STDIN:
        start(options, non_options[0], r"", [non_options[1]])
    # Substitute stuff from files and maybe stdin.
    elif len(non_options) > 2:
        start(options, non_options[0], non_options[1], non_options[2:])
    else:
        usage()

if __name__ == "__main__":
    exit(main(sys.argv[1:]))

