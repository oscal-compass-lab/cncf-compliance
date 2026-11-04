#!/usr/bin/env python3
"""Assess all enabled graduated CNCF projects. See assess_maturity.py."""

import sys

from assess_maturity import assess_maturity

if __name__ == "__main__":
    sys.exit(assess_maturity("graduated"))
