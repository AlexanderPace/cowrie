"""
This module tests the filesystem persistence feature.
These tests should be run locally on a machine with a running Cowrie instance.
The instance should be listening on port 2222 and allow access to a "TEST" user with the password "TEST".
Any filesystem persistence log files created for localhost/127.0.0.1 will be removed.
It should be noted that the activity generated from these tests will appear in logs.
"""

import os
import subprocess
import unittest
import paramiko


class TestFiles(unittest.TestCase):
    def test_touch_simple(self):
        """Touches a file and checks if it persists"""
        env_reset()
        login()
        self.assertEqual(True, False)

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
    print(os.listdir(root))
    fs_cmds_file = os.path.join(root, "127.0.0.1_fs_cmds")  # loopback addr
    cmd_hist_file = os.path.join(root, "127.0.0.1_cmd_hist")
    os.remove(fs_cmds_file)
    os.remove(cmd_hist_file)


def login():
    """Logs in to the Cowrie instance as an attacker"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname="localhost", port=2222, username="TEST", password="TEST")
    channel = ssh.invoke_shell()
    channel.send('ls -l\n') #TODO: REMOVE
    channel.recv(1024)  # first read just shows a prompt
    output = channel.recv(4096)
    print("####: ", output)
    print("Sanitised: ", readOutput(output))


def readOutput(input: bytes) -> str:
    """Reads in output from Paramiko SSH and returns the actual command output"""
    input = input.decode('utf-8')
    index0 = input.index('\x1b[4l')  # Remove prefix characters
    substring = input[index0+3:]
    index1 = substring.index('\r\n\x1b')  # Remove postfix characters and any remaining output
    output = substring[:index1]

    return output

if __name__ == '__main__':
    unittest.main()
