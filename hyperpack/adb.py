"""
ADB helper functions - device detection, APK pulling, MRC management
"""

import subprocess
import shutil
import re
from pathlib import Path
from . import console


ICONS_PATH = "/sdcard/Android/data/com.android.thememanager/files/MIUI/theme/.data/content/icons"


def _run(cmd, capture=True, check=False):
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        capture_output=capture,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_adb():
    """Check if adb is installed and on PATH."""
    return shutil.which("adb") is not None


def get_devices():
    """Return list of connected device serials."""
    code, out, _ = _run(["adb", "devices"])
    devices = []
    for line in out.splitlines()[1:]:
        if "\tdevice" in line:
            devices.append(line.split("\t")[0])
    return devices


def get_apk_paths(package_name):
    """Return all APK paths for a given package."""
    code, out, _ = _run(["adb", "shell", "pm", "path", package_name])
    if code != 0 or not out:
        return []
    paths = []
    for line in out.splitlines():
        if line.startswith("package:"):
            paths.append(line.replace("package:", "").strip())
    return paths


def pull_file(remote_path, local_path):
    """Pull a file from device. Returns True on success."""
    code, out, err = _run(["adb", "pull", remote_path, str(local_path)])
    return code == 0


def push_file(local_path, remote_path):
    """Push a file to device. Returns True on success."""
    code, out, err = _run(["adb", "push", str(local_path), remote_path])
    return code == 0


def list_mrc_files():
    """List .mrc files sorted by date (newest first). Returns list of (name, size, date)."""
    code, out, _ = _run(["adb", "shell", "ls", "-lt", ICONS_PATH])
    if code != 0:
        return []
    
    files = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 8 and parts[-1].endswith(".mrc"):
            try:
                size = int(parts[4])
                date = f"{parts[5]} {parts[6]}"
                name = parts[-1]
                files.append({"name": name, "size": size, "date": date, "path": f"{ICONS_PATH}/{name}"})
            except (ValueError, IndexError):
                continue
    return files


def get_newest_mrc():
    """Return the most recently modified .mrc file info dict, or None."""
    files = list_mrc_files()
    return files[0] if files else None


def pull_mrc(mrc_name, local_path):
    """Pull an MRC file from the device."""
    remote = f"{ICONS_PATH}/{mrc_name}"
    return pull_file(remote, local_path)


def push_mrc(local_path, mrc_name):
    """Push an MRC file to the device theme folder."""
    remote = f"{ICONS_PATH}/{mrc_name}"
    return push_file(local_path, remote)
