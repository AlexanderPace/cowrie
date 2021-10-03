"""
This module tests the filesystem persistence feature.
These tests should be run locally on a machine with a running Cowrie instance.
The instance should be listening on port 2222 and allow access to a "TEST" user with the password "TEST".
Any filesystem persistence log files created for localhost/127.0.0.1 will be removed.
It should be noted that the activity generated from these tests will appear in logs.
"""

import os
import unittest
import paramiko
from paramiko.channel import Channel
import time
from datetime import datetime

from paramiko.client import SSHClient


class TestFiles(unittest.TestCase):
    def test_touch_simple(self):
        """Touches a file and checks if it persists"""
        env_reset()
        channel, ssh = login()
        channel.sendall('touch file\n')
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M")
        channel.close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls -l\n') #TODO test the date/time is also correct
        channel.recv(1024)  # first read just shows a prompt
        output = channel.recv(4096)
        # print("####:", output)
        result = readOutput(output)
        # print("Sanitised:", bytes(result, 'utf-8'))

        self.assertIn("file", result, "File not present")
        output_with_date_time = "-rw-r--r-- 1 root root 0 " + date_time + " file"
        self.assertEqual(result, output_with_date_time)
        ssh.close()

#     def test_touch_in_dir(self):
#         """Makes a directory, then touches a file in it and checks if it persists"""
#         self.assertEqual(True, False)
#
#     def test_rm(self):
#         """Touches a file, reloads, then removes it and checks if the change persists"""
#         self.assertEqual(True, False)
#
#     def test_cp(self):
#         """Touches a file, copies it, and checks if it persists"""
#         self.assertEqual(True, False)
#
# class TestDirs(unittest.TestCase):
#     def test_mkdir_simple(self):
#         """Makes a directory and checks if it persists"""
#         self.assertEqual(True, False)
#
#     def test_mkdir_nested(self):
#         """Makes a directory, then makes another directory within it and checks if it persists"""
#         self.assertEqual(True, False)
#
#     def test_rmdir(self):
#         """Makes a directory, reloads, then removes it and checks if the change persists"""
#         self.assertEqual(True, False)


def env_reset():
    """Removes the record files so the system starts from a clean slate"""
    root = "/home/cowrie/cowrie/fspersistence/"
    fs_cmds_file = os.path.join(root, "127.0.0.1_fs_cmds")  # loopback addr
    cmd_hist_file = os.path.join(root, "127.0.0.1_cmd_hist")
    if os.path.isfile(fs_cmds_file):
        os.remove(fs_cmds_file)
    if os.path.isfile(cmd_hist_file):
        os.remove(cmd_hist_file)


def login() -> (Channel, SSHClient):
    """Logs in to the Cowrie instance as an attacker"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname="localhost", port=2222, username="TEST", password="TEST")
    channel = ssh.get_transport().open_session()
    channel.invoke_shell()

    return channel, ssh

    # channel.send('hostname\n') #TODO: REMOVE
    # channel.recv(1024)  # first read just shows a prompt
    # output = channel.recv(4096)
    # print("####: ", output)
    # print("Sanitised: ", readOutput(output))
    #
    # channel.send('hostname\n')  # TODO: REMOVE
    # #channel.recv(1024)  # first read just shows a prompt
    # output = channel.recv(4096)
    # print("####: ", output)
    # print("Sanitised: ", readOutput(output))


def readOutput(input: bytes) -> str:
    """Reads in output from Paramiko SSH and returns the actual command output"""
    input = input.decode('utf-8')
    index0 = input.find('\x1b[4l')  # Remove prefix characters
    if index0 == -1:
        index0 = 0
    substring = input[index0+4:]
    index1 = substring.find('\r\n')  # Remove postfix characters and any remaining output
    output = ""
    if index1 == -1:
        output = substring
    else:
        output = substring[:index1]

    output.strip(' \r\n\x1b')
    return output

if __name__ == '__main__':
    unittest.main()
