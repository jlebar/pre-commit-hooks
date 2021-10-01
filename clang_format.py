#!/usr/bin/env python3

"""Runs git-clang-format, invoking a particular clang-format binary.

Download the clang-format binary if necessary.

Usage example:

  clang_format.py 11.0.0 [diff|whole-file] foo.cpp bar.h
"""

import argparse
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
# typing module available for python 3.6 or lower does not include Final.
# This leads to ImportError. In case this happens, we can try to import
# Final from typing_extensions, which is a backport of the newest typing
# functionalities into older python versions (3.5 and 3.6).
try:
    from typing import Final, Mapping, Optional, Sequence, Tuple
except ImportError:
    from typing_extensions import Final
    from typing import Mapping, Optional, Sequence, Tuple

    # clang-format sha1s were retrieved at
#  https://commondatastorage.googleapis.com/chromium-clang-format/
# The below shas are tested across different os to identify the version.
# For getting the list a script is written to download all the sha's
# from https://commondatastorage.googleapis.com/chromium-clang-format/.
# and validate them in different os to identify the version corresponding to OS.
# The helper script to validate will be added as a future patch

CLANG_FORMAT_SHAS: Final[Mapping[Tuple[int, int, int], Mapping[str, str],]] = {
    (3, 5, 0): {
        "Linux": "b26f74f07f51a99d79d34be57a28bc82dee42854",
        "Darwin": "ce0718a133a059aca5da5f307a36bbc310df3e12",
        "Windows": "fc8a7cd2219eaa70daa01173844fad4c815394d7",
    },
    (3, 6, 0): {
        "Linux": "f237f50fab9ceca4066788b7bf936ef2aa366239",
        "Darwin": "eb3fd19492128421c3eab80f4cdeed7b07428988",
        "Windows": "e93c345e8d4d003632cabae8ff4f64c3b74f0c16",
    },
    (3, 7, 0): {
        "Linux": "acc9e19e04ad4cf6be067366d2522348cd160ae1",
        "Darwin": "e66adcd1631b8d80650e7b15106033b04c9c2212",
        "Windows": "2d5e931765ee1c7c4465fd6d77c8b7606c487b3f",
    },
    (3, 9, 0): {
        "Linux": "8b68e8093516183b8f38626740eeaff97f112f7e",
        "Darwin": "afe0942b94fe33619361efe1510ae081c3070dc1",
        "Windows": "f80b6ab38d7c7e0903c25e968028c1eaa25bb874",
    },
    (4, 0, 0): {
        "Linux": "06b8b3e315c1b55b58459d61fe3297e0988c6c63",
        "Darwin": "e0cfdaf63938e06d05a986a0038658ec6b7cad17",
        "Windows": "a15d5130e787633a119e8e0ae9b267696c4c2863",
    },
    (5, 0, 0): {
        "Linux": "5349d1954e17f6ccafb6e6663b0f13cdb2bb33c8",
        "Darwin": "0679b295e2ce2fce7919d1e8d003e497475f24a3",
        "Windows": "c8455d43d052eb79f65d046c6b02c169857b963b",
    },
    (8, 0, 0): {
        "Linux": "327721c99d40602c1829b4b682771d52e1d5f1b8",
        "Darwin": "025ca7c75f37ef4a40f3a67d81ddd11d7d0cdb9b",
        "Windows": "b5f5d8d5f8a8fcd2edb5b6cae37c0dc3e129c945",
    },
    (11, 0, 0): {
        "Linux": "1baf0089e895c989a311b6a38ed94d0e8be4c0a7",
        "Darwin": "62bde1baa7196ad9df969fc1f06b66360b1a927b",
        "Windows": "d4afd4eba27022f5f6d518133aebde57281677c9",
    },
}


def download_clang_format(sha: str, dest: Path) -> None:
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


def check_hash(sha: str, file: Path) -> None:
    d = hashlib.sha1()
    with open(file, "rb") as f:
        while True:
            chunk = f.read(1024 * 64)
            if not chunk:
                break
            d.update(chunk)

    if d.hexdigest() != sha:
        print(
            f"FATAL: sha1sum mismatch on {file}.\
Expected {sha}, but was {d.hexdigest()}",
            file=sys.stderr,
        )
        print("Maybe the file is corrupted?  Try deleting it.")
        sys.exit(1)


def get_version_key(version: str) -> Tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return (int(major), int(minor), int(patch))


def clang_format_path(version: Tuple[int, int, int]) -> Path:
    """
    Gets the path of the relevant clang-format binary.
    Downloads it if necessary.
    """
    try:
        base_cachedir = Path(os.environ["XDG_CACHE_HOME"])
    except KeyError:
        base_cachedir = Path.home().joinpath(".cache")

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

    clang_format_sha = CLANG_FORMAT_SHAS[version][platform.system()]
    clang_format_file = cachedir / f"clang-format-{clang_format_sha}"

    if not clang_format_file.exists():
        download_clang_format(clang_format_sha, clang_format_file)

    check_hash(clang_format_sha, clang_format_file)
    return clang_format_file


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Arguments for pre commit.")
    parser.add_argument(
        "version",
        choices=tuple(
            ".".join(f"{element}" for element in version)
            for version in CLANG_FORMAT_SHAS.keys()
        ),
        help="Clang format version to run",
    )
    parser.add_argument("scope", choices=["diff", "whole-file"], help="Run on files")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Files pre-commit believes are changed.",
    )
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        assert e.code is not None
        return e.code

    this_dir = os.path.dirname(__file__)
    git_cf_path = os.path.join(this_dir, "git-clang-format")
    if args.scope == "diff":
        print("Formatting changed lines in " + " ".join([str(x) for x in args.files]))
        clang_format_run = subprocess.run(
            (
                sys.executable,
                git_cf_path,
                "-f",
                "--binary",
                f"{clang_format_path(get_version_key(args.version))}",
                "--",
                *args.files,
            ),
            check=True,
        )
    elif args.scope == "whole-file":
        print("Formatting all lines in " + " ".join([str(x) for x in args.files]))
        clang_format_run = subprocess.run(
            (
                f"{clang_format_path(get_version_key(args.version))}",
                "-i",
                "--",
                *args.files,
            ),
            check=True,
        )
    return clang_format_run.returncode


if __name__ == "__main__":
    main()
