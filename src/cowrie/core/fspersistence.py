"""
This module enables Cowrie to provide simulated filesystem persistence.
A user logging on more than once will see almost the same filesystem as they did the previous time they logged on.
This is achieved by replaying filesystem-related commands upon user return.

(c) Alexander Pace, 2021
"""

import json
import logging
import os

from cowrie.commands.fs import Command_touch
from cowrie.shell.honeypot import HoneyPotShell, StdOutStdErrEmulationProtocol


def record_fs_commands(ip_addr: str) -> None:
    """
    Scans log for the user matching the specified IP address and copies out all filesystem-related commands to a file
    `[ip]_fs_cmds.txt` in `cowrie/fspersistence`.
    If this file is already present, it is appended.

    @param ip_addr: a string containing the source IP address of the selected user
    @return None
    """

    # Load the current log file
    log_data = []

    try:
        with open('var/log/cowrie/cowrie.json', 'r') as log:
            for line in log.readlines():
                log_data.append(json.loads(line))
    except IOError as e:
        logging.exception('Could not load log file ', e)  # TODO: Is this the right way to log an exception in the Cowrie log?

    # Search for filesystem commands from the specified user and append them to the filesystem command record file
    FS_COMMANDS = ['touch', 'mkdir', 'cp', 'rm', 'rmdir', 'cd']  # TODO: add curl support

    session_commands = ""
    for entry in log_data:
        if entry.get('src_ip') == ip_addr:
            message = entry.get('message')
            if 'New connection' in message:
                session_commands = ""  # Reset the output to only get the last session for this IP
            elif 'CMD' in message:
                for command in FS_COMMANDS:
                    if command in message:
                        session_commands = session_commands + message[5:] + '\n'
                        break

    # Create or load the filesystem command record file
    if not os.path.exists('fspersistence'):
        os.makedirs('fspersistence')

    try:
        fs_record = open('fspersistence/' + ip_addr + '_fs_cmds.txt', 'a')
        fs_record.write(session_commands)
        fs_record.close()
    except IOError as e:
        logging.exception('Could not load or create fs command record file', e)  # TODO: also check logging is correct here


def replay_fs_commands(ip_addr: str, protocol: 'HoneyPotInteractiveProtocol', commands: dict) -> None:
    """
    Executes, in order, any previous filesystem-related commands executed by the user matching the specified IP address.

    @param ip_addr: a string containing the source IP address of the selected user
    @return None
    """

    args = "new_file"
    protocol.pp = StdOutStdErrEmulationProtocol(protocol, Command_touch, None, None, None)
    protocol.cmdstack.append(HoneyPotShell(protocol, interactive=False, redirect=True))
    command = Command_touch(protocol, args)
    command.start()


def append_command_history(ip_addr: str, command: str) -> None:
    """
    Appends the command history of the user matching the specified IP address to a file `[ip]_cmd_hist` in
    `cowrie/fspersistence`.

    @param ip_addr: a string containing the source IP address of the selected user
    @param command: a string containing the command to be recorded
    @return None
    """

    if not os.path.exists('fspersistence'):
        os.makedirs('fspersistence')

    try:
        history = open('fspersistence/' + ip_addr + '_cmd_hist', 'a')
        history.write(command)
    except IOError as e:
        logging.exception('Could not load or create command history file', e)  # TODO: also check logging exeception


def get_command_history(ip_addr: str) -> list:
    """
    Loads the user's command history into a list.

    @param ip_addr: a string containing the source IP address of the selected user
    @return command history as a list of strings
    """

    history = []

    try:
        with open('fspersistence/' + ip_addr + '_cmd_hist', 'r') as history_file:
            for line in history_file.readlines():
                history.append(line.rstrip())
    except IOError as e:
        logging.exception('Could not load command history file ', e)  # TODO: Again, exception correct way?

    return history


def clear_command_history(ip_addr: str) -> None:
    """
    Clears the command history file of the user matching the specified IP address.

    @param ip_addr: a string containing the source IP address of the selected user
    @return: None
    """

    try:
        with open('fspersistence/' + ip_addr + '_cmd_hist', 'rb+') as history:
            history.truncate(0)
            history.close()
    except IOError as e:
        logging.exception('Could not load command history file ', e)  # TODO: Again, exception correct way?
