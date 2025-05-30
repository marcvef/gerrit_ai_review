#!/usr/bin/env python3
"""
Gerrit Client - A module for interacting with Gerrit API

This module provides functionality to connect to a Gerrit instance,
retrieve changes, and post reviews.
"""

import json
import requests
import urllib.parse
from typing import Dict, Any

# Import common utilities and configuration
from gerrit_ai_review.utils.review_common import ReviewConfig, print_green, print_yellow, print_red

class GerritClient:
    """Client for interacting with Gerrit."""

    def __init__(self, config: ReviewConfig):
        """
        Initialize the Gerrit client.

        Args:
            config: Review configuration containing Gerrit settings
        """
        self.config = config
        self.auth = requests.auth.HTTPBasicAuth(config.gerrit_username, config.gerrit_password)

    def test_connection(self) -> bool:
        """
        Test the connection to Gerrit.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to get the server version
            path = '/config/server/version'
            response = requests.get(f"{self.config.gerrit_url}/a{path}", auth=self.auth)

            if response.status_code == 200:
                # Gerrit uses " )]}'" to guard against XSSI
                version = json.loads(response.content[5:])
                print_green(f"Successfully connected to Gerrit at {self.config.gerrit_url}", self)
                print_green(f"Gerrit version: {version}", self)
                return True
            else:
                print_red(f"Failed to connect to Gerrit: {response.status_code} {response.reason}", self)
                return False
        except Exception as e:
            print_red(f"Error connecting to Gerrit: {e}", self)
            return False

    def get_change_by_id(self, change_id: str) -> Dict[str, Any]:
        """
        Get a specific change by its ID.

        Args:
            change_id: The ID of the change to get

        Returns:
            The change details or None if not found
        """
        # If the change_id is a number, assume it's a change number
        if change_id.isdigit():
            path = f"/changes/{change_id}?o=CURRENT_REVISION&o=CURRENT_COMMIT&o=CURRENT_FILES"
        else:
            # Otherwise, assume it's a full change ID
            path = (f"/changes/{urllib.parse.quote(self.config.gerrit_project, safe='')}~" +
                   f"{urllib.parse.quote(self.config.gerrit_branch, safe='')}~{change_id}" +
                   "?o=CURRENT_REVISION&o=CURRENT_COMMIT&o=CURRENT_FILES")

        response = requests.get(f"{self.config.gerrit_url}/a{path}", auth=self.auth)

        if response.status_code != 200:
            print_red(f"Error getting change: {response.status_code} {response.reason}", self)
            print_red(response.text, self)
            return None

        # Gerrit uses " )]}'" to guard against XSSI
        return json.loads(response.content[5:])

    def get_checkout_url(self, change: Dict[str, Any], patch_version: str = None) -> str:
        """
        Get the URL to checkout a specific change.

        Args:
            change: The change details returned by get_change_by_id
            patch_version: The specific patch version to checkout (if None, uses the latest)

        Returns:
            The URL to checkout the change
        """
        if not change:
            return None

        # Get the current revision
        current_revision = change.get('current_revision')
        if not current_revision:
            return None

        # If a specific patch version is requested, we need to construct the URL differently
        change_number = change.get('_number')
        if patch_version and change_number:
            print_green(f"Using specific patch version: {patch_version}", self)
            # Construct a URL for the specific patch version
            return f"git fetch {self.config.gerrit_url}/{self.config.gerrit_project} refs/changes/{change_number%100:02d}/{change_number}/{patch_version} && git checkout FETCH_HEAD"

        # Otherwise, use the standard approach for the latest version
        # Get the fetch information for the current revision
        fetch_info = change.get('revisions', {}).get(current_revision, {}).get('fetch', {})

        # Try to get the anonymous HTTP URL first, then try other protocols
        for protocol in ['anonymous http', 'http', 'ssh']:
            if protocol in fetch_info:
                url = fetch_info[protocol].get('url')
                ref = fetch_info[protocol].get('ref')
                if url and ref:
                    return f"git fetch {url} {ref} && git checkout FETCH_HEAD"

        # If we couldn't find a fetch URL, construct a URL based on the change number
        if change_number:
            return f"git fetch {self.config.gerrit_url}/{self.config.gerrit_project} refs/changes/{change_number%100:02d}/{change_number}/{current_revision[-8:]} && git checkout FETCH_HEAD"

        return None

    def post_review(self, change: Dict[str, Any], message: str = "Hello World! This is a test comment.") -> bool:
        """
        Post a review comment on a change.

        Args:
            change: The change details returned by get_change_by_id
            message: The review message to post

        Returns:
            True if the review was posted successfully, False otherwise
        """
        if not change:
            print_red("Cannot post review: No change provided", self)
            return False

        # Get the current revision
        current_revision = change.get('current_revision')
        if not current_revision:
            print_red("Cannot post review: No current revision found", self)
            return False

        # Prepare the review input
        review_input = {
            'message': message,
            'notify': 'OWNER'
        }

        # Post the review
        path = f"/changes/{change['id']}/revisions/{current_revision}/review"
        try:
            response = requests.post(
                f"{self.config.gerrit_url}/a{path}",
                json=review_input,
                auth=self.auth,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                print_green("Review posted successfully", self)
                return True
            else:
                print_red(f"Error posting review: {response.status_code} {response.reason}", self)
                print_red(response.text, self)
                return False
        except Exception as e:
            print_red(f"Error posting review: {e}", self)
            return False

    @staticmethod
    def extract_change_id_from_url(url: str) -> tuple:
        """
        Extract a change ID and patch version from a Gerrit URL.

        Handles URLs like:
        - https://review.whamcloud.com/c/fs/lustre-release/+/59005
        - https://review.whamcloud.com/c/fs/lustre-release/+/58460/5 (with patch version)
        - https://review.whamcloud.com/59005
        - https://review.whamcloud.com/#/c/59005/
        - https://review.whamcloud.com/q/59005

        Args:
            url: The Gerrit URL or change ID

        Returns:
            A tuple of (change_id, patch_version) where patch_version is None if not specified
        """
        # If the input is not a URL, return it as is (assuming it's already a change ID)
        if not url.startswith('http'):
            return url, None

        # Try to extract the change ID and patch version from the URL
        try:
            # First, try to match the specific pattern for URLs with patch versions
            # Example: https://review.whamcloud.com/c/fs/lustre-release/+/58460/5
            import re
            pattern = r'/\+/(\d+)/(\d+)$'
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)

            # Remove any trailing slashes and query parameters
            url = url.rstrip('/')
            if '?' in url:
                url = url.split('?')[0]

            # Split the URL into parts
            parts = url.split('/')

            # Handle URLs like https://review.whamcloud.com/59005
            if parts[-1].isdigit():
                return parts[-1], None

            # Handle URLs like https://review.whamcloud.com/c/fs/lustre-release/+/59005
            if '+' in parts:
                # Find the part after the '+' symbol
                for i in range(len(parts) - 1):
                    if parts[i] == '+' and i+1 < len(parts) and parts[i+1].isdigit():
                        return parts[i+1], None

            # Handle URLs like https://review.whamcloud.com/#/c/59005/
            if '#' in url:
                hash_parts = url.split('#')[1].split('/')
                for i, part in enumerate(hash_parts):
                    if part.isdigit():
                        # Check if there's a patch version after the change ID
                        if i+1 < len(hash_parts) and hash_parts[i+1].isdigit():
                            return part, hash_parts[i+1]
                        return part, None

            # Handle URLs like https://review.whamcloud.com/q/59005
            if '/q/' in url:
                query_part = parts[-1]
                if query_part.isdigit():
                    return query_part, None

            # If we couldn't extract a change ID, return the original URL
            print_yellow(f"Could not extract change ID from URL: {url}")
            return url, None
        except Exception as e:
            print_red(f"Error extracting change ID from URL: {e}")
            return url, None