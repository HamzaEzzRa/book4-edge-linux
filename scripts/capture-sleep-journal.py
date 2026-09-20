#!/usr/bin/env python3
"""Fsync each journal line. Run as a system service outside user.slice.
Usage: capture-sleep-journal.py NEW_LOG_FILE
"""
import datetime
import os
import subprocess
import sys

if len(sys.argv) != 2:
    sys.exit(f"usage: {sys.argv[0]} NEW_LOG_FILE")

fd = os.open(sys.argv[1], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "wb") as out:
    out.write(f"capture started {datetime.datetime.now().astimezone().isoformat()}\n".encode())
    out.flush()
    os.fsync(out.fileno())
    # Persist the new directory entry as well as its contents.
    parent = os.open(os.path.dirname(os.path.abspath(sys.argv[1])), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)
    with subprocess.Popen([
        "journalctl", "--follow", "--lines=0", "--output=short-monotonic", "--no-pager",
        "_TRANSPORT=kernel", "+", "_PID=1", "+",
        "_SYSTEMD_UNIT=systemd-hibernate.service", "+",
        "_SYSTEMD_UNIT=book4-pd-charge.service", "+", "SYSLOG_IDENTIFIER=book4-test",
    ], stdout=subprocess.PIPE) as journal:
        try:
            for line in journal.stdout:
                out.write(line)
                out.flush()
                os.fsync(out.fileno())
        finally:
            if journal.poll() is None:
                journal.terminate()
        sys.exit(journal.wait())
