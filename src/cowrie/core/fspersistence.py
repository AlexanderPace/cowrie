"""
This module enables Cowrie to provide simulated filesystem persistence.
A user logging on more than once will see almost the same filesystem as they did the previous time they logged on.
This is achieved by replaying filesystem-related commands upon user return.

(c) Alexander Pace, 2021
"""

import json
import logging
import os
from os.path import abspath, dirname, join


def record_fs_commands(ip_addr: str):
    """
    Scans log for specified user and copies out all filesystem-related commands to a file '[ip] fs cmds.txt'.
    If this file is already present, it is appended.

    @param ip_addr: a string containing the source IP address of the selected user
    """

    # Load the current log file
    log_data = []

    try:
        with open('var/log/cowrie/cowrie.json', 'r') as log:
            for line in log.readlines():
                log_data.append(json.loads(line))
    except IOError as e:
        logging.exception('Could not load log file ', e)  # TODO: Is this the right way to log an exception in the Cowrie log?

    # Create or load the filesystem command record file
    fs_record = None

    if not os.path.exists('fspersistence'):
        os.makedirs('fspersistence')

    try:
        fs_record = open('fspersistence/' + ip_addr + ' fs cmds.txt', 'w+')  # TODO: currently apostrophes are being included in the filename
    except IOError as e:
        logging.exception('Could not load or create fs command record file', e)

    if fs_record is None:
        return  # TODO: should probably handle this better

    # Search for filesystem commands from the specified user and append them to the filesystem command record file
    FS_COMMANDS = ['touch', 'mkdir', 'cp', 'rm']  # TODO: add curl support

    # TODO: this should also only take entries from the most recent logoff
    for entry in log_data:
        if entry.get('src_ip') == ip_addr:
            message = entry.get('message')
            if 'CMD' in message:
                for command in FS_COMMANDS:
                    if command in message:
                        fs_record.write(message + '\n')  # TODO: Still contains "CMD " in this string
                        break

    fs_record.close()


def save_command_history(ip_addr):
    """
    Saves the command history of the current user to a file 'cmd_hist'.
    If this file is already present, it is appended.

    @param ip_addr: a string containing the source IP address of the selected user
    """



def replay_fs_commands(ip_addr):
    """
    Executes, in order, any previous filesystem-related commands executed by this user.

    @param ip_addr: a string containing the source IP address of the selected user
    """




def restore_command_history(ip_addr):
    """
    Restores a user's commands from a previous session to the command history file.

    @param ip_addr: a string containing the spurce IP address of the selected user
    """
