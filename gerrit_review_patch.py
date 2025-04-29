#!/usr/bin/env python3
"""
Gerrit Review Patch - A tool for connecting to Gerrit and reviewing patches

This is the main entry point for the Gerrit AI Review tool.
"""

import argparse
import os
import subprocess
from typing import Dict, Any, Optional

# Import common utilities and configuration
from gerrit_ai_review.utils.review_common import ReviewConfig, print_green, print_yellow, print_red

# Import Gerrit client
from gerrit_ai_review.gerrit.client import GerritClient

# Import the run_review function from ask_ai.py
from gerrit_ai_review.ai.ask_ai import run_review

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Connect to Gerrit and review patches")
    parser.add_argument("-c", "--config", type=str, help="Path to configuration file")
    parser.add_argument("--test", action="store_true", help="Test the connection to Gerrit")
    parser.add_argument("-s", "--skip-gerrit-review", action="store_true",
                       help="Run AI review but skip posting the results to Gerrit")
    parser.add_argument("change_id", type=str, nargs='?',
                       help="Change ID, number, or Gerrit URL to retrieve and review")

    return parser.parse_args()


class GerritReviewer:
    """
    A class to link GerritClient and AiderReview.

    This class handles:
    1. Checking out patches from Gerrit
    2. Running AiderReview on the patches
    3. Posting review comments back to Gerrit
    """

    def __init__(self, gerrit_client: GerritClient, lustre_dir: str, config_file=None):
        """
        Initialize the GerritReviewer.

        Args:
            gerrit_client: The GerritClient to use for Gerrit operations
            lustre_dir: The directory of the Lustre git repository
            config_file: Path to the configuration file
        """
        self.gerrit_client = gerrit_client
        self.lustre_dir = lustre_dir
        self.config_file = config_file

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
            print_red(f"Change {change_id} not found.", self)
            return None

        # Get the checkout command
        checkout_cmd = self.gerrit_client.get_checkout_url(change)
        if not checkout_cmd:
            print_red(f"Could not get checkout command for change {change_id}.", self)
            return None

        print_green(f"Checking out change {change_id}...", self)
        print_green(f"Command: {checkout_cmd}", self)

        # Verify that the Lustre directory exists
        if not os.path.isdir(self.lustre_dir):
            print_red(f"Lustre directory not found: {self.lustre_dir}", self)
            return None

        # Save the current working directory
        original_dir = os.getcwd()

        try:
            # Change to the Lustre git directory
            print_green(f"Changing to Lustre directory: {self.lustre_dir}", self)
            os.chdir(self.lustre_dir)

            # Clean the git directory of any changes
            print_green("Cleaning git directory...", self)

            # Check if there are any uncommitted changes
            status_cmd = "git status --porcelain"
            status_result = subprocess.run(status_cmd, shell=True, capture_output=True, text=True)

            if status_result.stdout.strip():
                print_yellow("Uncommitted changes found in the repository.", self)
                print_yellow("Running git reset --hard to clean the working directory...", self)

                # Reset any uncommitted changes
                reset_cmd = "git reset --hard"
                reset_result = subprocess.run(reset_cmd, shell=True, capture_output=True, text=True)

                if reset_result.returncode != 0:
                    print_red(f"Error resetting git repository: {reset_result.stderr}", self)
                    return None
            else:
                print_green("Git repository has no uncommitted changes.", self)

            # Clean untracked files and directories
            print_yellow("Running git clean -df to remove untracked files and directories...", self)
            clean_cmd = "git clean -df"
            clean_result = subprocess.run(clean_cmd, shell=True, capture_output=True, text=True)

            if clean_result.returncode != 0:
                print_red(f"Error cleaning git repository: {clean_result.stderr}", self)
                return None

            print_green("Git repository cleaned successfully.", self)

            # Execute the checkout command
            print_green("Executing checkout command...", self)
            checkout_result = subprocess.run(checkout_cmd, shell=True, capture_output=True, text=True)

            if checkout_result.returncode != 0:
                print_red(f"Error checking out patch: {checkout_result.stderr}", self)
                return None

            print_green("Patch checked out successfully.", self)

            # Verify that we're on the right commit
            verify_cmd = "git log -1 --oneline"
            verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
            print_green(f"Current commit: {verify_result.stdout.strip()}", self)

            return change

        except Exception as e:
            print_red(f"Error during checkout: {e}", self)
            return None

        finally:
            # Return to the original directory
            os.chdir(original_dir)

    def run_review_bot(self, change: Dict[str, Any]) -> Optional[str]:
        """
        Run AiderReview on a checked out patch.

        Args:
            change: The change details

        Returns:
            The review comment if successful, None otherwise
        """
        print_green("Running AiderReview on the patch...", self)

        try:
            # Get the change subject as a description
            subject = change.get('subject', 'No subject')
            print_green(f"Change subject: {subject}", self)

            # Get the current revision
            current_revision = change.get('current_revision')
            if not current_revision:
                print_red("Cannot get current revision from change details")
                return None

            # We have the current revision, which is enough to proceed

            # Get the change number for logging
            change_number = change.get('_number', 'unknown')

            # Run the review
            print_green(f"Running review for change {change_number}...", self)
            review_result = run_review(
                use_paid_model=True,  # Use the free model by default
                max_files=5,           # Allow more files for Gerrit reviews
                max_tokens=200000,     # Use the default token limit
                output_file=None,      # Don't save to a file
                skip_confirmation=False, # Skip confirmation in automated mode
                config_file=self.config_file  # Pass the configuration file
            )

            if not review_result:
                print_red("AiderReview did not produce a review", self)
                return None

            print_green("Review completed successfully", self)

            # Return the review result
            return review_result

        except Exception as e:
            print_red(f"Error running ReviewBot: {e}", self)
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
        print_green(f"Posting review comment to change {change.get('_number')}...", self)
        return self.gerrit_client.post_review(change, review_comment)

    def review_patch(self, change_id: str, skip_gerrit_review: bool = False) -> bool:
        """
        Review a patch from Gerrit.

        This method:
        1. Checks out the patch
        2. Runs AiderReview on it
        3. Posts the review comment back to Gerrit (unless skip_gerrit_review is True)

        Args:
            change_id: The ID of the change to review
            skip_gerrit_review: If True, skip posting the review to Gerrit

        Returns:
            True if successful, False otherwise
        """
        # Checkout the patch
        change = self.checkout_patch(change_id)
        if not change:
            return False

        # Run AiderReview on the patch
        review_comment = self.run_review_bot(change)
        if not review_comment:
            return False

        # If skip_gerrit_review is True, don't post the review to Gerrit
        if skip_gerrit_review:
            return True

        # Post the review comment back to Gerrit
        return self.post_review(change, review_comment)


def main():
    """Main function."""
    args = parse_arguments()

    # Load configuration (now contains both Review and Gerrit settings)
    config = ReviewConfig(args.config)

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
        change_id = GerritClient.extract_change_id_from_url(args.change_id)
        print_green(f"Getting change: {change_id}")

        # Create a GerritReviewer instance
        reviewer = GerritReviewer(client, config.lustre_dir, args.config)

        # Review the patch
        print_green(f"Reviewing patch {change_id}...")
        success = reviewer.review_patch(change_id, args.skip_gerrit_review)

        if success:
            if args.skip_gerrit_review:
                print_green("AI review completed successfully (not posted to Gerrit).")
            else:
                print_green("Review completed and posted to Gerrit successfully.")
        else:
            print_red("Review failed.")

        return

    # If no action specified, show help
    print_yellow("No action specified. Use --test to test the connection or provide a change ID/URL as a positional argument.")

if __name__ == "__main__":
    main()