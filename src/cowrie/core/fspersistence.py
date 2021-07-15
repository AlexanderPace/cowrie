"""
This module enables Cowrie to provide simulated filesystem persistence.
A user logging on more than once will see almost the same filesystem as they did the previous time they logged on.
This is achieved by replaying filesystem-related commands upon user return.

(c) Alexander Pace, 2021
"""

def record_fs_commands():
    """
    Scans log for current user and copies out all filesystem-related commands to a file 'fs_cmds'.
    If this file is already present, it is appended.
    """

def save_command_history():
    """
    Saves the command history of the current user to a file 'cnd_hist'.
    If this file is already present, it is appended.
    """

def replay_fs_commands():
    """
    Executes, in order, any previous filesystem-related commands executed by this user.
    """

def restore_command_history():
    """
    Restores a user's commands from a previous session to the command history file.
    """
