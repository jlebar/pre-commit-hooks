#!/usr/bin/env python3

"""Checks each file in sys.argv for the string "DO NOT SUBMIT"."""

import sys
import os
import subprocess


def err(s):
    print(s, file=sys.stderr)


# There are many ways we could search for the string "DO NOT SUBMIT", but `git
# grep --no-index` is nice because
#  - it's very fast (as compared to iterating over the file in Python)
#  - we can reasonably assume it's available on all machines
#  - unlike plain grep, which is slower and has different flags on MacOS versus
#    Linux, git grep is always the same.
res = subprocess.run(
    ["git", "grep", "-Hn", "--no-index", "DO NOT SUBMIT", *sys.argv[1:]],
    capture_output=True,
)
if res.returncode == 0:
    err('Error: The string "DO NOT SUBMIT" was found!')
    err(res.stdout.decode("utf-8"))
    sys.exit(1)
elif res.returncode == 2:
    err(f"Error invoking grep on {fname}:")
    err(res.stderr.decode("utf-8"))
    sys.exit(2)
