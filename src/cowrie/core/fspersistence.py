"""
This module enables Cowrie to provide filesystem persistence.
A user logging on more than once will see the same filesystem as they did the previous time they logged on.

(c) Alexander Pace, 2021
"""

# Two functions, to be triggered at logon and logoff
# Logon checks for an existing cache record JSON. If there is one, it applies the changes described, drawing on cached files.
# It then pours the full VM filesystem structure into a JSON file with hashes on each item.
# Logoff hashes the whole filesystem again, and compares it to the JSON file created at logon. Any differences are cached. The JSON generated at logon is discarded.
# The cached files are recorded in another JSON file.

def logon():
    # Use os.walk() as per this StackOverflow answer: https://stackoverflow.com/questions/29634781/finding-md5-of-files-recursively-in-directory-in-python

def logoff():


