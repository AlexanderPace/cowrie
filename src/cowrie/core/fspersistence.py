"""
This module enables Cowrie to provide simulated filesystem persistence.
A user logging on more than once will see almost the same filesystem as they did the previous time they logged on.
This is achieved by replaying filesystem-related commands upon user return.

(c) Alexander Pace, 2021
"""

import json
import logging
import os
import dateutil.parser

from cowrie.commands.fs import *
from cowrie.core.config import CowrieConfig
from cowrie.shell.command import HoneyPotCommand
from cowrie.shell.honeypot import HoneyPotShell, StdOutStdErrEmulationProtocol


def record_fs_commands(ip_addr: str) -> None:
    """
    Scans log for the user matching the specified IP address and copies out all filesystem-related commands to a file
    `[ip]_fs_cmds` in `cowrie/fspersistence`.
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
        logging.exception('Could not load log file ', e)

    # Search for filesystem commands from the specified user and append them to the filesystem command record file
    FS_COMMANDS = ['touch ', 'mkdir ', 'cp ', 'rm ', 'rmdir ', 'cd ']  # TODO: add curl support

    session_commands = ""
    for entry in log_data:
        if entry.get('src_ip') == ip_addr:
            message = ''.join(entry.get('message'))
            if not len(message) == 0:
                if message.startswith('New connection'):
                    session_commands = ""  # Reset the output to only get the last session for this IP
                elif message.startswith('CMD: '):
                    for command in FS_COMMANDS:
                        if message.startswith(command, 5):
                            session_commands = session_commands + entry.get("timestamp") + "," + message[5:] + '\n'
                            break

    # Create or load the filesystem command record file
    if not os.path.exists('fspersistence'):
        os.makedirs('fspersistence')

    try:
        fs_record = open('fspersistence/' + ip_addr + '_fs_cmds', 'a')
        fs_record.write(session_commands)
        fs_record.close()
    except IOError as e:
        logging.exception('Could not load or create fs command record file', e)

    purge()


def replay_fs_commands(ip_addr: str, protocol: 'HoneyPotInteractiveProtocol') -> None:
    """
    Executes, in order, any previous filesystem-related commands executed by the user matching the specified IP address.

    @param ip_addr: a string containing the source IP address of the selected user
    @param protocol: the process protocol needed to execute the command
    @return None
    """

    try:
        with open('fspersistence/' + ip_addr + '_fs_cmds', 'r') as fs_record:
            for line in fs_record:
                split = line.split(",")
                timestamp = dateutil.parser.isoparse(split[0])
                timestamp = timestamp.strftime("%y%m%d%H%M")
                command_string = split[1]
                tokens = command_string.split(' ')
                command_name = tokens[0]
                args = tokens[1:]

                # Apply correct timestamp
                if tokens[0] in ["touch", "mkdir"]:
                    args.insert(0, timestamp)
                    args.insert(0, "-t")

                command = fs_cmd_switch(command_name, args, protocol)
                command.start()
                command.protocol.pp.suppress_error_output = False

            # Reset the user back to their home directory
            fs_cmd_switch("cd", ['~'], protocol).start()
    except IOError:
        logging.info("No filesystem command record file found, likely new user")


def fs_cmd_switch(command: str, args: list, protocol: 'HoneyPotInteractiveProtocol') -> HoneyPotCommand:
    """
    Returns the command object for the provided command name.
    Provides a speed advantage over if/else blocks.

    @param command: the name of the command
    @param args: a list of the command's arguments
    @param protocol: the process protocol needed to execute the command
    @return: a `HoneyPotCommand` object associated with this command
    """

    # Implementation based on https://jaxenter.com/implement-switch-case-statement-python-138315.html

    # Strip the newline from the final arg
    args[len(args) - 1] = args[len(args) - 1].rstrip()

    index = 0
    for arg in args:
        if command == "cd" and arg in ["", " "]:
            args[index] = "~"
        index += 1

    # Add an empty argument if a command with no arguments has been stored to avoid an error
    if len(args) == 0:
        args.append("")

    def touch_sw():
        protocol.pp = StdOutStdErrEmulationProtocol(protocol, Command_touch, None, None, None)
        protocol.pp.suppress_error_output = True
        protocol.cmdstack.append(HoneyPotShell(protocol, interactive=False, redirect=True))
        return Command_touch(protocol, *args)

    def mkdir_sw():
        protocol.pp = StdOutStdErrEmulationProtocol(protocol, Command_mkdir, None, None, None)
        protocol.pp.suppress_error_output = True
        protocol.cmdstack.append(HoneyPotShell(protocol, interactive=False, redirect=True))
        return Command_mkdir(protocol, *args)

    def cp_sw():
        protocol.pp = StdOutStdErrEmulationProtocol(protocol, Command_cp, None, None, None)
        protocol.pp.suppress_error_output = True
        protocol.cmdstack.append(HoneyPotShell(protocol, interactive=False, redirect=True))
        return Command_cp(protocol, *args)

    def rm_sw():
        protocol.pp = StdOutStdErrEmulationProtocol(protocol, Command_rm, None, None, None)
        protocol.pp.suppress_error_output = True
        protocol.cmdstack.append(HoneyPotShell(protocol, interactive=False, redirect=True))
        return Command_rm(protocol, *args)

    def rmdir_sw():
        protocol.pp = StdOutStdErrEmulationProtocol(protocol, Command_rmdir, None, None, None)
        protocol.pp.suppress_error_output = True
        protocol.cmdstack.append(HoneyPotShell(protocol, interactive=False, redirect=True))
        return Command_rmdir(protocol, *args)

    def cd_sw():
        protocol.pp = StdOutStdErrEmulationProtocol(protocol, Command_cd, None, None, None)
        protocol.pp.suppress_error_output = True
        protocol.cmdstack.append(HoneyPotShell(protocol, interactive=False, redirect=True))
        return Command_cd(protocol, *args)

    switch = {
        'touch': touch_sw,
        'mkdir': mkdir_sw,
        'cp': cp_sw,
        'curl': print("TODO: add curl support"),  # TODO implementation needed
        'rm': rm_sw,
        'rmdir': rmdir_sw,
        'cd': cd_sw
    }
    command = switch.get(command, lambda: "Command not found")  # return None if invalid command
    return command()


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
        logging.exception('Could not load or create command history file', e)


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
        logging.exception('Could not load command history file ', e)

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
        logging.exception('Could not load command history file ', e)


def purge() -> None:
    """
    Deletes old command history and filesystem command record files.
    Maxmimum file age determined by config parameter persistence_record_max_age.

    @return: None
    """

    # Based on implementation from https://codingshiksha.com/python/python-3-automation-script-to-delete-all-files-inside-a-directory-older-than-x-days-using-os-and-time-modules-full-project-for-beginners/

    files = os.listdir("fspersistence/")
    now = time.time()
    max_days = int(CowrieConfig.get("honeypot", "persistence_record_max_age", fallback="14"))
    max_seconds = max_days * 86400

    for file in files:
        file_path = os.path.join("fspersistence/", file)
        if os.path.isfile(file_path) and os.stat(file_path).st_mtime < now - max_seconds:
            os.remove(file_path)
