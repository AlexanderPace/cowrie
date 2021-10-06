"""
This module tests the filesystem persistence feature.
These tests should be run locally on a machine with a running Cowrie instance.
The instance should be listening on port 2222 and allow access to a "TEST" user with the password "TEST".
Any filesystem persistence log files created for localhost/127.0.0.1 will be removed.
It should be noted that the activity generated from these tests will appear in logs.
"""

import os
from shutil import copyfile
import unittest
import time
import paramiko
from paramiko.channel import Channel
from datetime import datetime
from paramiko.client import SSHClient
import warnings


class TestFiles(unittest.TestCase):
    def test_touch_simple(self):
        """Touches a file and checks if it persists"""
        env_reset()
        channel, ssh = login()
        channel.sendall('touch file\n')
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M")
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls -l\n')
        channel.recv(1024)  # first read just shows a prompt
        output = channel.recv(4096)
        result = read_output(output)

        channel.close()
        ssh.get_transport().close()
        ssh.close()
        self.assertIn("file", result, "File not present")
        output_with_date_time = "-rw-r--r-- 1 root root 0 " + date_time + " file"
        self.assertEqual(result, output_with_date_time, "Date and time incorrect")

    def test_touch_in_dir(self):
        """Makes a directory, then touches a file in it and checks if it persists"""
        env_reset()
        channel, ssh = login()
        channel.sendall('mkdir dir\n')
        channel.sendall('cd dir\n')
        channel.sendall('touch file\n')
        channel.recv(1024)
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M")
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls -l dir\n')
        channel.recv(1024)
        output = channel.recv(4096)
        result = read_output(output)

        channel.close()
        ssh.get_transport().close()
        ssh.close()
        self.assertIn("file", result, "File not present")
        output_with_date_time = "-rw-r--r-- 1 root root 0 " + date_time + " file"
        self.assertEqual(result, output_with_date_time, "Date and time incorrect")


    def test_rm(self):
        """Touches a file, reloads, then removes it and checks if the change persists"""
        env_reset()
        channel, ssh = login()
        channel.sendall('touch file\n')
        channel.recv(1024)
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls\n')
        channel.recv(1024)
        output = channel.recv(4096)
        result = read_output(output)

        self.assertIn("file", result, "File not present")
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('rm file\n')
        channel.recv(1024)
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls\n')
        channel.recv(1024)
        output = channel.recv(4096)
        result = read_output(output)
        channel.close()
        ssh.get_transport().close()
        ssh.close()
        self.assertNotIn("file", result, "File still present")

    def test_cp(self):
        """Touches a file, copies it, and checks if it persists"""
        env_reset()
        channel, ssh = login()
        channel.sendall('touch file\n')
        channel.sendall('cp file file2\n')
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls\n')
        channel.recv(1024)
        output = channel.recv(4096)
        result = read_output(output)

        channel.close()
        ssh.get_transport().close()
        ssh.close()
        self.assertIn("file", result, "Original file not present")
        self.assertIn("file2", result, "Copied file not present")


class TestDirs(unittest.TestCase):
    def test_mkdir_simple(self):
        """Makes a directory and checks if it persists"""
        env_reset()
        channel, ssh = login()
        channel.sendall('mkdir dir\n')
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M")
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls -l\n')
        channel.recv(1024)
        output = channel.recv(4096)
        result = read_output(output)

        channel.close()
        ssh.get_transport().close()
        ssh.close()
        self.assertIn("dir", result, "Directory not present")
        output_with_date_time = "drwxr-xr-x 1 root root 4096 " + date_time + " dir"
        self.assertEqual(result, output_with_date_time, "Date and time incorrect")

    def test_mkdir_nested(self):
        """Makes a directory, then makes another directory within it and checks if it persists"""
        env_reset()
        channel, ssh = login()
        channel.sendall('mkdir dir\n')
        channel.sendall('cd dir\n')
        channel.sendall('mkdir dir2\n')
        channel.recv(1024)
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M")
        channel.close()
        ssh.get_transport().close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls -l dir\n')
        channel.recv(1024)
        output = channel.recv(4096)
        result = read_output(output)

        channel.close()
        ssh.get_transport().close()
        ssh.close()
        self.assertIn("dir2", result, "Directory not present")
        output_with_date_time = "drwxr-xr-x 1 root root 4096 " + date_time + " dir2"
        self.assertEqual(result, output_with_date_time, "Date and time incorrect")

    def test_rmdir(self):
        """Makes a directory, reloads, then removes it and checks if the change persists"""
        env_reset()
        channel, ssh = login()
        channel.sendall('mkdir dir\n')
        channel.recv(1024)
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls\n')
        channel.recv(1024)
        output = channel.recv(4096)
        result = read_output(output)

        self.assertIn("dir", result, "Directory not present")
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('rmdir dir\n')
        channel.recv(1024)
        channel.close()
        ssh.get_transport().close()
        ssh.close()

        channel, ssh = login()
        channel.sendall('ls\n')
        channel.recv(1024)
        output = channel.recv(4096)
        result = read_output(output)
        channel.close()
        ssh.get_transport().close()
        ssh.close()
        self.assertNotIn("dir", result, "Directory still present")


class TestSpeed(unittest.TestCase):
    def test_speed_control(self):
        """Tests the average time it takes for no commands to be replayed upon login"""
        env_reset()
        samples = []
        for i in range(9):
            before = time.perf_counter()
            channel, ssh = login()
            time_elapsed = time.perf_counter() - before
            channel.close()
            ssh.close()
            samples.append(time_elapsed)

        avg_time = sum(samples) / len(samples)
        print("Average time for control:", avg_time)
        self.assertLess(avg_time, 4)

    def test_speed_100(self):
        """Tests the average time it takes for 100 commands to be replayed upon login"""
        env_reset()
        copyfile("100 commands", "/home/cowrie/cowrie/fspersistence/127.0.0.1_fs_cmds")
        samples = []
        for i in range(9):
            before = time.perf_counter()
            channel, ssh = login()
            time_elapsed = time.perf_counter() - before
            channel.close()
            ssh.close()
            samples.append(time_elapsed)

        avg_time = sum(samples) / len(samples)
        print("Average time for 100 commands:", avg_time)
        self.assertLess(avg_time, 4)

    def test_speed_1000(self):
        """Tests the average time it takes for 1,000 commands to be replayed upon login"""
        env_reset()
        copyfile("1000 commands", "/home/cowrie/cowrie/fspersistence/127.0.0.1_fs_cmds")
        samples = []
        for i in range(9):
            before = time.perf_counter()
            channel, ssh = login()
            time_elapsed = time.perf_counter() - before
            channel.close()
            ssh.close()
            samples.append(time_elapsed)

        avg_time = sum(samples) / len(samples)
        print("Average time for 1,000 commands:", avg_time)
        self.assertLess(avg_time, 4)

    def test_speed_10000(self):
        """Tests the average time it takes for 10,000 commands to be replayed upon login"""
        env_reset()
        copyfile("10000 commands", "/home/cowrie/cowrie/fspersistence/127.0.0.1_fs_cmds")
        samples = []
        for i in range(9):
            before = time.perf_counter()
            channel, ssh = login()
            time_elapsed = time.perf_counter() - before
            channel.close()
            ssh.close()
            samples.append(time_elapsed)

        avg_time = sum(samples) / len(samples)
        print("Average time for 10,000 commands:", avg_time)
        self.assertLess(avg_time, 4)


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
    warnings.filterwarnings(action="ignore", category=ResourceWarning)
    ssh.connect(hostname="localhost", port=2222, username="TEST", password="TEST")
    channel = ssh.get_transport().open_session()
    channel.invoke_shell()

    return channel, ssh


def read_output(input: bytes) -> str:
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
    # Try/catch is needed because for some reason env_reset() isn't called when simply placed after the call to main()
    try:
        unittest.main()
    finally:
        env_reset()