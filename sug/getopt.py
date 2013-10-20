"Option parser module for sug."

class FlagNeedsArguments(Exception):
    "Raised when arguments to a flag are missing."
    pass

class UnknownFlag(Exception):
    "Raised when an unrecognised flag is passed via command line."
    pass

class Getopt:
    """
    Getopt -- Unix style minimalistic option parser.

    Getopt is an argument parser, inspired by it's namesake, POSIX getopt(3).
    Here is an example of it's usage:

    opt_parser = Getopt("-a", "-plongjohn", "-la,b,c", "hello", "moto",
                        a = (False, "do all thingy things"),
                        p = (True, "give funky props to these people"),
                        l = (True, "a list of stuff"))
    opt_parser.parse()
    opt_parser.options()     #=> {"a": True, "p": "longjohn", "l":[a,b,c]}
    opt_parser.non_options() #=> ["hello", "moto"]

    Flags start with the `-' character and are one character long. All flags
    with arguments are stored as lists of strings.  Switch flags are
    represented as booleans.  Parsing options stops when an argument without a
    leading `-' or the flag `--' is encountered. The rest of the arguments
    (including the current argument in case it is not `--') are all
    interpreted as non-options.
    """
    def __init__(self, program_name, *args, **options):
        """
	Initialise Getopt.

        args: A list of arguments.

        options: This is a map from option strings to tuples. Each tuple
        consists of a boolean value and a description of the string, which is
        either a string, or an object with a __str__ method.  The boolean
        value indicates whether the option has an argument or not, and
        description will be used to construct a help string.
        """
        self.__program_name = program_name
        self.__options = options
        self.__argv    = args
        self.__parsed = False

        self.__END_OF_FLAGS_MARKER = "--"
        self.__FLAG_ARG_SEPERATOR  = ","

        self._options = {} # flag: value
        self._non_options = ()

    def parse(self):
        "Actually parse arguments."
        switches = {switch for switch, settings in self.__options.items()
                    if not settings[0]}
        flags_w_args = {switch for switch, settings in self.__options.items()
                        if settings[0]}
        set_switches = set()
        options      = dict()
        for i in range(len(self.__argv)):
            arg = self.__argv[i]
            # The first non-option terminates argument parsing...
            if not arg.startswith("-"):
                self._non_options = tuple(self.__argv[i:])
                break
            # ...and so does the end-of-flags marker.
            elif arg == self.__END_OF_FLAGS_MARKER:
                self._non_options = tuple(self.__argv[i + 1 :])
                break
            else:
                # Get rid of initial `-'.
                arg  = arg[1:]
                flag = arg[0]
                # If the flag is in switches, start pushing it and the rest of
                # it to set_switches.
                if flag in switches:
                    for i in range(len(arg)):
                        if arg[i] in switches:
                            set_switches.add(arg[i])
                        # If see a flag that expects arguments, use the rest of
                        # the arguments as argument to that flag.
                        elif arg[i] in flags_w_args:
                            arg  = arg[i:]
                            flag = arg[0]
                            break
                    # If the break in the loop above did not get executed, the
                    # whole arg comprised switches, thus the program shall
                    # continue with the next argument.
                    continue
                if flag in flags_w_args:
                    flag_value = arg[1:].split(self.__FLAG_ARG_SEPERATOR)
                    if flag_value == [""]:
                        raise FlagNeedsArguments(
                            "Flag `{0}' expects argument(s).".format(flag))
                    else:
                        options[flag] = flag_value
                else:
                    raise UnknownFlag("Flag `{0}' is not recognised."
                                      .format(flag))
        unset_switches = switches - set_switches
        self._options = options
        for switch in unset_switches:
            self._options[switch] = False
        for switch in set_switches:
            self._options[switch] = True
        self.__parsed = True
        return True

    def options(self):
        """
        Return parsed options.  If self.parse() has not been run already, run
        it.
        """
        if not self.__parsed:
            self.parse()
        return self._options

    def non_options(self):
        """
        Return parsed non-option arguments.  If self.parse() has not been run
        already, run it.
        """
        if not self.__parsed:
            self.parse()
        return self._non_options

