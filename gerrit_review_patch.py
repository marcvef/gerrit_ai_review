#!/usr/bin/env python3
"""
Gerrit Review Patch - A tool for connecting to Gerrit and reviewing patches

This module provides functionality to connect to a Gerrit instance,
retrieve changes, and post reviews.
"""

import argparse
import json
import os
import requests
import subprocess
import sys
import urllib.parse
import yaml
from typing import Dict, Any, Optional

# Import common utilities and configuration
from review_common import ReviewBotConfig, print_green, print_yellow, print_red

# Import the run_review function from ask_aider.py
from ask_aider import run_review


# GerritConfig class has been removed and merged into ReviewBotConfig in review_common.py


class GerritClient:
    """Client for interacting with Gerrit."""

    def __init__(self, config: ReviewBotConfig):
        """
        Initialize the Gerrit client.

        Args:
            config: ReviewBot configuration containing Gerrit settings
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
                print_green(f"Successfully connected to Gerrit at {self.config.gerrit_url}")
                print_green(f"Gerrit version: {version}")
                return True
            else:
                print_red(f"Failed to connect to Gerrit: {response.status_code} {response.reason}")
                return False
        except Exception as e:
            print_red(f"Error connecting to Gerrit: {e}")
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
            print_red(f"Error getting change: {response.status_code} {response.reason}")
            print_red(response.text)
            return None

        # Gerrit uses " )]}'" to guard against XSSI
        return json.loads(response.content[5:])

    def get_checkout_url(self, change: Dict[str, Any]) -> str:
        """
        Get the URL to checkout a specific change.

        Args:
            change: The change details returned by get_change_by_id

        Returns:
            The URL to checkout the change
        """
        if not change:
            return None

        # Get the current revision
        current_revision = change.get('current_revision')
        if not current_revision:
            return None

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
        change_number = change.get('_number')
        if change_number:
            return f"git fetch {self.config.gerrit_url}/a/{self.config.gerrit_project} refs/changes/{change_number%100:02d}/{change_number}/{current_revision[-8:]} && git checkout FETCH_HEAD"

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
            print_red("Cannot post review: No change provided")
            return False

        # Get the current revision
        current_revision = change.get('current_revision')
        if not current_revision:
            print_red("Cannot post review: No current revision found")
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
                print_green("Review posted successfully")
                return True
            else:
                print_red(f"Error posting review: {response.status_code} {response.reason}")
                print_red(response.text)
                return False
        except Exception as e:
            print_red(f"Error posting review: {e}")
            return False


def extract_change_id_from_url(url: str) -> str:
    """
    Extract a change ID from a Gerrit URL.

    Handles URLs like:
    - https://review.whamcloud.com/c/fs/lustre-release/+/59005
    - https://review.whamcloud.com/59005
    - https://review.whamcloud.com/#/c/59005/
    - https://review.whamcloud.com/q/59005

    Args:
        url: The Gerrit URL or change ID

    Returns:
        The extracted change ID, or the original string if it's not a URL or no change ID could be extracted
    """
    # If the input is not a URL, return it as is (assuming it's already a change ID)
    if not url.startswith('http'):
        return url

    # Try to extract the change ID from the URL
    try:
        # Remove any trailing slashes and query parameters
        url = url.rstrip('/')
        if '?' in url:
            url = url.split('?')[0]

        # Split the URL into parts
        parts = url.split('/')

        # Handle URLs like https://review.whamcloud.com/59005
        if parts[-1].isdigit():
            return parts[-1]

        # Handle URLs like https://review.whamcloud.com/c/fs/lustre-release/+/59005
        if '+' in parts and parts[-2] == '+' and parts[-1].isdigit():
            return parts[-1]

        # Handle URLs like https://review.whamcloud.com/#/c/59005/
        if '#' in url:
            hash_parts = url.split('#')[1].split('/')
            for part in hash_parts:
                if part.isdigit():
                    return part

        # Handle URLs like https://review.whamcloud.com/q/59005
        if '/q/' in url:
            query_part = parts[-1]
            if query_part.isdigit():
                return query_part

        # If we couldn't extract a change ID, return the original URL
        print_yellow(f"Could not extract change ID from URL: {url}")
        return url
    except Exception as e:
        print_red(f"Error extracting change ID from URL: {e}")
        return url


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Connect to Gerrit and review patches")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--test", action="store_true", help="Test the connection to Gerrit")
    parser.add_argument("change_id", type=str, nargs='?',
                       help="Change ID, number, or Gerrit URL to retrieve and review")

    return parser.parse_args()


class GerritReviewer:
    """
    A class to link GerritClient and ReviewBot.

    This class handles:
    1. Checking out patches from Gerrit
    2. Running ReviewBot on the patches
    3. Posting review comments back to Gerrit
    """

    def __init__(self, gerrit_client: GerritClient, lustre_dir: str):
        """
        Initialize the GerritReviewer.

        Args:
            gerrit_client: The GerritClient to use for Gerrit operations
            lustre_dir: The directory of the Lustre git repository
        """
        self.gerrit_client = gerrit_client
        self.lustre_dir = lustre_dir

    def checkout_patch(self, change_id: str) -> Optional[Dict[str, Any]]:
        """
        Checkout a patch from Gerrit.

        Args:
            change_id: The ID of the change to checkout

        Returns:
            The change details if successful, None otherwise
        """
        # Get the change details
        change = self.gerrit_client.get_change_by_id(change_id)
        if not change:
            print_red(f"Change {change_id} not found.")
            return None

        # Get the checkout command
        checkout_cmd = self.gerrit_client.get_checkout_url(change)
        if not checkout_cmd:
            print_red(f"Could not get checkout command for change {change_id}.")
            return None

        print_green(f"Checking out change {change_id}...")
        print_green(f"Command: {checkout_cmd}")

        # Verify that the Lustre directory exists
        if not os.path.isdir(self.lustre_dir):
            print_red(f"Lustre directory not found: {self.lustre_dir}")
            return None

        # Save the current working directory
        original_dir = os.getcwd()

        try:
            # Change to the Lustre git directory
            print_green(f"Changing to Lustre directory: {self.lustre_dir}")
            os.chdir(self.lustre_dir)

            # Clean the git directory of any changes
            print_green("Cleaning git directory...")

            # Check if there are any uncommitted changes
            status_cmd = "git status --porcelain"
            status_result = subprocess.run(status_cmd, shell=True, capture_output=True, text=True)

            if status_result.stdout.strip():
                print_yellow("Uncommitted changes found in the repository.")
                print_yellow("Running git reset --hard to clean the working directory...")

                # Reset any uncommitted changes
                reset_cmd = "git reset --hard"
                reset_result = subprocess.run(reset_cmd, shell=True, capture_output=True, text=True)

                if reset_result.returncode != 0:
                    print_red(f"Error resetting git repository: {reset_result.stderr}")
                    return None
            else:
                print_green("Git repository has no uncommitted changes.")

            # Clean untracked files and directories
            print_yellow("Running git clean -df to remove untracked files and directories...")
            clean_cmd = "git clean -df"
            clean_result = subprocess.run(clean_cmd, shell=True, capture_output=True, text=True)

            if clean_result.returncode != 0:
                print_red(f"Error cleaning git repository: {clean_result.stderr}")
                return None

            print_green("Git repository cleaned successfully.")

            # Execute the checkout command
            print_green("Executing checkout command...")
            checkout_result = subprocess.run(checkout_cmd, shell=True, capture_output=True, text=True)

            if checkout_result.returncode != 0:
                print_red(f"Error checking out patch: {checkout_result.stderr}")
                return None

            print_green("Patch checked out successfully.")

            # Verify that we're on the right commit
            verify_cmd = "git log -1 --oneline"
            verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
            print_green(f"Current commit: {verify_result.stdout.strip()}")

            return change

        except Exception as e:
            print_red(f"Error during checkout: {e}")
            return None

        finally:
            # Return to the original directory
            os.chdir(original_dir)

    def run_review_bot(self, change: Dict[str, Any]) -> Optional[str]:
        """
        Run ReviewBot on a checked out patch.

        Args:
            change: The change details

        Returns:
            The review comment if successful, None otherwise
        """
        print_green("Running ReviewBot on the patch...")

        try:
            # Get the change subject as a description
            subject = change.get('subject', 'No subject')
            print_green(f"Change subject: {subject}")

            # Get the current revision
            current_revision = change.get('current_revision')
            if not current_revision:
                print_red("Cannot get current revision from change details")
                return None

            # We have the current revision, which is enough to proceed

            # Get the change number for logging
            change_number = change.get('_number', 'unknown')

            # Run the review
            print_green(f"Running review for change {change_number}...")
            review_result = run_review(
                use_paid_model=True,  # Use the free model by default
                max_files=5,           # Allow more files for Gerrit reviews
                max_tokens=200000,     # Use the default token limit
                output_file=None,      # Don't save to a file
                skip_confirmation=False # Skip confirmation in automated mode
            )

            if not review_result:
                print_red("ReviewBot did not produce a review")
                return None

            print_green("Review completed successfully")

            # Return the review result
            return review_result

        except Exception as e:
            print_red(f"Error running ReviewBot: {e}")
            return None

    def post_review(self, change: Dict[str, Any], review_comment: str) -> bool:
        """
        Post a review comment back to Gerrit.

        Args:
            change: The change details
            review_comment: The review comment to post

        Returns:
            True if successful, False otherwise
        """
        print_green(f"Posting review comment to change {change.get('_number')}...")
        return self.gerrit_client.post_review(change, review_comment)

    def review_patch(self, change_id: str) -> bool:
        """
        Review a patch from Gerrit.

        This method:
        1. Checks out the patch
        2. Runs ReviewBot on it
        3. Posts the review comment back to Gerrit

        Args:
            change_id: The ID of the change to review

        Returns:
            True if successful, False otherwise
        """
        # Checkout the patch
        change = self.checkout_patch(change_id)
        if not change:
            return False

        # Run ReviewBot on the patch
        review_comment = self.run_review_bot(change)
        if not review_comment:
            return False

        # Post the review comment back to Gerrit
        return self.post_review(change, review_comment)


def main():
    """Main function."""
    args = parse_arguments()

    # Load configuration (now contains both ReviewBot and Gerrit settings)
    config = ReviewBotConfig(args.config)

    # Create Gerrit client
    client = GerritClient(config)

    # Test connection if requested
    if args.test:
        if client.test_connection():
            print_green("Connection test successful!")
        else:
            print_red("Connection test failed!")
        return

    # Get a specific change if requested
    if args.change_id:
        # Extract the change ID from the URL if necessary
        change_id = extract_change_id_from_url(args.change_id)
        print_green(f"Getting change: {change_id}")

        # Create a GerritReviewer instance
        reviewer = GerritReviewer(client, config.lustre_dir)

        # Review the patch
        print_green(f"Reviewing patch {change_id}...")
        success = reviewer.review_patch(change_id)

        if success:
            print_green("Review completed successfully.")
        else:
            print_red("Review failed.")

        return

    # If no action specified, show help
    print_yellow("No action specified. Use --test to test the connection or provide a change ID/URL as a positional argument.")

if __name__ == "__main__":
    main()