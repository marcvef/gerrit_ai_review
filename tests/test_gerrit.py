#!/usr/bin/env python3
"""
Tests for Gerrit-related functionality.
"""

import sys
import os

# Add the parent directory to the path so we can import modules from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function to test
from gerrit_review_patch import extract_change_id_from_url
from review_common import print_green, print_red


def test_extract_change_id_from_url():
    """Test the extract_change_id_from_url function with various URL formats."""
    test_cases = [
        # Direct change IDs
        ("12345", "12345"),
        ("I1234567890abcdef", "I1234567890abcdef"),

        # Simple URLs
        ("https://review.whamcloud.com/59005", "59005"),
        ("https://review.whamcloud.com/59005/", "59005"),

        # Full URLs
        ("https://review.whamcloud.com/c/fs/lustre-release/+/59005", "59005"),
        ("https://review.whamcloud.com/c/fs/lustre-release/+/59005/", "59005"),

        # Hash URLs
        ("https://review.whamcloud.com/#/c/59005/", "59005"),

        # Query URLs
        ("https://review.whamcloud.com/q/59005", "59005"),
        ("https://review.whamcloud.com/q/59005?status=open", "59005"),
    ]

    for input_url, expected_output in test_cases:
        actual_output = extract_change_id_from_url(input_url)
        if actual_output != expected_output:
            print_red(f"Test failed for input '{input_url}':")
            print_red(f"  Expected: '{expected_output}'")
            print_red(f"  Actual:   '{actual_output}'")
        else:
            print_green(f"Test passed for input '{input_url}'")


if __name__ == "__main__":
    test_extract_change_id_from_url()
