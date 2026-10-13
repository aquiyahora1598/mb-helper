"""Separate bundled resources from files that must survive portable updates."""

import os
import sys


def application_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def data_path(filename):
    return os.path.join(application_dir(), filename)
