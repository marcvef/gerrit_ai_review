#!/usr/bin/env python3
"""
Wrapper script to run ask_ai.py from the command line.
"""

import sys
from gerrit_ai_review.ai.ask_ai import run_manual

if __name__ == "__main__":
    # Run the main function from ask_ai.py
    sys.exit(run_manual())
