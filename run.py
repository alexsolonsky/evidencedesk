#!/usr/bin/env python3
"""Start EvidenceDesk from a clean checkout without installing packages."""
import os
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    raise SystemExit('EvidenceDesk requires Python 3.9 or later.')
os.chdir(Path(__file__).resolve().parent)
from app import main

if __name__ == '__main__':
    main()
