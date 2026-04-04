#!/usr/bin/env python3
"""Helpers for connecting to UiO WebDAV via an SSH tunnel."""

import os
import sys
import subprocess
import time
import socket
import random
from contextlib import AbstractContextManager

from webdav4.fsspec import WebdavFileSystem
from urllib.parse import urlparse, urlunparse


LOGIN_HOST = "login.uio.no"
DAV_HOST = "www-dav.mn.uio.no"
DAV_PORT = 443


def pick_free_port():
    """Pick a random free TCP port on localhost."""
    for _ in range(10):
        port = random.randint(20000, 40000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_port(host, port, timeout=60):
    """Wait until (host, port) starts accepting TCP connections."""
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.5)
    return False


def start_ssh_tunnel(twofa_user, local_port):
    """
    Start a simple SSH tunnel:

      local -> twofa_user@login.uio.no -> www-dav.mn.uio.no:443

    Command:

      ssh -o ExitOnForwardFailure=yes \
          -L <local_port>:www-dav.mn.uio.no:443 \
          twofa_user@login.uio.no -N
    """
    cmd = [
        "ssh",
        "-o", "ExitOnForwardFailure=yes",
        "-L", f"{local_port}:{DAV_HOST}:{DAV_PORT}",
        f"{twofa_user}@{LOGIN_HOST}",
        "-N",
    ]

    # Inherit stdin/stdout/stderr so you see SSH prompts and can type responses
    proc = subprocess.Popen(cmd)

    if not wait_for_port("127.0.0.1", local_port, timeout=60):
        print(
            "Tunnel did not become ready in time. "
            "SSH may be waiting for password/2FA or failed."
        )
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        sys.exit(1)

    if proc.poll() is not None:
        print("SSH tunnel process exited early with code", proc.returncode)
        sys.exit(1)

    return proc


def make_webdav_fs(base_url, username, password, local_port):
    """
    Create a WebdavFileSystem that talks to WebDAV via the SSH tunnel
    on 127.0.0.1:<local_port>, authenticating as `username`/`password`
    and sending Host: www-dav.mn.uio.no so UiO's HAProxy routes correctly.
    """
    parsed = urlparse(base_url)

    # IMPORTANT: force IPv4 localhost to avoid ::1 / IPv6 issues
    new_netloc = f"127.0.0.1:{local_port}"
    tunneled_url = urlunparse((parsed.scheme, new_netloc, parsed.path, "", "", ""))

    fs = WebdavFileSystem(
        base_url=tunneled_url.rstrip('/'),
        auth=(username, password),
        # Passed directly to webdav4.Client(...), then httpx.Client(...)
        verify=False,                 # ignore potential cert/hostname mismatch
        headers={"Host": DAV_HOST},   # make HAProxy see the real host
    )
    return fs


class WebdavTunnel(AbstractContextManager):
    """
    Context manager that opens an SSH tunnel to UiO and exposes a WebDAV FS.

    Usage:
        with WebdavTunnel(base_url, webdav_user, webdav_password, twofa_user) as fs:
            # use fs (WebdavFileSystem)
            ...
    """
    def __init__(self, base_url, webdav_user, webdav_password, twofa_user):
        self.base_url = base_url
        self.webdav_user = webdav_user
        self.webdav_password = webdav_password
        self.twofa_user = twofa_user
        self.local_port = None
        self.ssh_proc = None
        self.fs = None

    def __enter__(self):
        self.local_port = pick_free_port()
        self.ssh_proc = start_ssh_tunnel(
            twofa_user=self.twofa_user,
            local_port=self.local_port,
        )
        self.fs = make_webdav_fs(
            base_url=self.base_url,
            username=self.webdav_user,
            password=self.webdav_password,
            local_port=self.local_port,
        )
        return self.fs

    def __exit__(self, exc_type, exc, exc_tb):
        if self.ssh_proc is not None:
            self.ssh_proc.terminate()
            try:
                self.ssh_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ssh_proc.kill()
        return False  # do not suppress exceptions
