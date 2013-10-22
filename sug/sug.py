"Command line interface for sug."

import sys
import os
import re
import tempfile
import errno
import difflib
import select

from sug.getopt import Getopt, UnknownFlag

ANY_STDIN = select.select([sys.stdin], [], [], 0)[0]

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
    "Check a file for existance and die if it doesn't exist."
    try:
        os.stat(_file)
    except FileNotFoundError:
        die("cannot stat file `{0}'".format(_file), 3)

def start(options, regexp_or_script, substitute, files):
    "Start processig files."
    # If anything piped, operate on that too.
    if ANY_STDIN:
        do_substitute(options, regexp_or_script, substitute, None, True)
    for _file in files:
        check_exists_or_die(_file)
        if not os.path.isfile(_file):
            die("cannot operate on directories")
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
    sys.stdout.write("sug: usage: sug [-bopsF] "
                     "(REGEXP|FILE) SUBSTITUTE FILES...\n")
    exit(4)

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
    n = len(non_options)

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

