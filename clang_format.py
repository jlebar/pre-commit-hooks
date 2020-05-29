#!/usr/bin/env python3

"""Runs git-clang-format, invoking a particular clang-format binary.

Download the clang-format binary if necessary.

Usage example:

  clang_format.py 10.0.0 foo.cpp bar.h
"""

import glob
import hashlib
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request

from pathlib import Path

# clang-format sha1s were retrieved at Chromium rev
# 81cc23a856578b149a37dd109b147d8544f9cbd8.
#
# https://github.com/chromium/chromium/blob/master/buildtools/linux64/clang-format.sha1
# https://github.com/chromium/chromium/blob/master/buildtools/mac/clang-format.sha1
# https://github.com/chromium/chromium/blob/master/buildtools/win/clang-format.exe.sha1
CLANG_FORMAT_SHAS = {
    "Linux": "1baf0089e895c989a311b6a38ed94d0e8be4c0a7",
    "Darwin": "62bde1baa7196ad9df969fc1f06b66360b1a927b",
    "Windows": "d4afd4eba27022f5f6d518133aebde57281677c9",
}


def download_clang_format(sha: str, dest: Path):
    download_path = (
        f"https://commondatastorage.googleapis.com/chromium-clang-format/{sha}"
    )
    print("Downloading clang-format (~2mb)...")

    # We download the file from the web into a temp dir, then atomically rename
    # it to `dest`.  In order for this to work, the temp dir must be on the
    # same filesystem as `dest`.
    #
    # You might be tempted to use NamedTemporaryFile instead of a
    # TemporaryDirectory.  The problem is, we want to use delete=True, and
    # NamedTemporaryFile will raise an exception if it *can't* delete the file,
    # which is what happens in the success case!
    #
    # (The reason we're paranoid about using atomic renames is that pre-commit
    # can and will invoke this script in parallel, and we want to protect
    # against the script stepping on its own toes.)
    with tempfile.TemporaryDirectory(dir=dest.parent) as tempdir_name:
        tempdir = Path(tempdir_name)
        with urllib.request.urlopen(download_path) as download_file:
            with tempdir.joinpath("clang-format").open("wb") as outfile:
                shutil.copyfileobj(download_file, outfile)

            st = os.stat(outfile.name)
            os.chmod(outfile.name, st.st_mode | stat.S_IEXEC)

            print(f"Moving downloaded clang-format to {dest.resolve()}")
            Path(outfile.name).rename(dest)


def check_hash(sha: str, file: Path):
    d = hashlib.sha1()
    with open(file, "rb") as f:
        while True:
            chunk = f.read(1024 * 64)
            if not chunk:
                break
            d.update(chunk)

    if d.hexdigest() != sha:
        print(
            f"FATAL: sha1sum mismatch on {file}.  Expected {sha}, but was {d.hexdigest()}",
            file=sys.stderr,
        )
        print("Maybe the file is corrupted?  Try deleting it.")
        sys.exit(1)


def clang_format_path() -> Path:
    """Gets the path of the relevant clang-format binary.

  Downloads it if necessary.
  """
    try:
        base_cachedir = Path(os.environ["XDG_CACHE_HOME"])
    except KeyError:
        base_cachedir = Path(os.environ["HOME"]).joinpath(".cache")

    cachedir = base_cachedir.joinpath("pre-commit-jlebar")

    if not cachedir.exists():
        cachedir.mkdir()
        with cachedir.joinpath("README").open("w") as f:
            f.write(
                """\
This directory is maintained by jlebar's pre-commit hooks.
Learn more: https://github.com/jlebar/pre-commit-hooks
"""
            )

    clang_format_sha = CLANG_FORMAT_SHAS[platform.system()]
    clang_format_file = cachedir.joinpath("clang-format-" + clang_format_sha)

    if not clang_format_file.exists():
        download_clang_format(clang_format_sha, clang_format_file)

    check_hash(clang_format_sha, clang_format_file)
    return clang_format_file


def main():
    this_dir = os.path.dirname(__file__)
    git_cf_path = os.path.join(this_dir, "git-clang-format")
    print("Formatting " + " ".join(sys.argv[1:]))
    subprocess.run(
        [sys.executable, git_cf_path, "-f", "--binary", str(clang_format_path()), "--",]
        + sys.argv[1:]
    )


if __name__ == "__main__":
    main()
