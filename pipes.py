"""
Compatibility shim for the pipes module which was removed in Python 3.13.
This provides the minimal functionality needed by coloredlogs.
"""

import shlex

# The main function coloredlogs uses from pipes
def quote(s):
    """Return a shell-escaped version of the string s."""
    return shlex.quote(s)

# Additional functions that might be used
def mkarg(s):
    """Deprecated alias for quote()."""
    return quote(s)

# Module-level constants that might be referenced
FILEIN_FILEOUT = 0
STDIN_FILEOUT = 1
FILEIN_STDOUT = 2
STDIN_STDOUT = 3
