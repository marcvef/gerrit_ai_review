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
    parser.add_argument("--yes", action="store_true",
                       help="Skip confirmation prompts")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Print verbose output, including command results")

    # Review type options
    review_type_group = parser.add_argument_group("Review types (if none specified, all will be run)")
    review_type_group.add_argument("--generic-review", action="store_true", default=False,
                                  help="Run generic review")
    review_type_group.add_argument("--style-review", action="store_true", default=False,
                                  help="Run style check review")
    review_type_group.add_argument("--static-analysis-review", action="store_true", default=False,
                                  help="Run static analysis review")

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

    def checkout_patch(self, change_id: str, patch_version: str = None) -> Optional[Dict[str, Any]]:
        """
        Checkout a patch from Gerrit.

        Args:
            change_id: The ID of the change to checkout
            patch_version: The specific patch version to checkout (if None, uses the latest)

        Returns:
            The change details if successful, None otherwise
        """
        # Get the change details
        change = self.gerrit_client.get_change_by_id(change_id)
        if not change:
            print_red(f"Change {change_id} not found.", self)
            return None

        # Get the checkout command, passing the patch version if specified
        checkout_cmd = self.gerrit_client.get_checkout_url(change, patch_version)
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

    def run_review_bot(self, change: Dict[str, Any], generic_review=True, style_review=False,
                   static_analysis_review=False, skip_confirmation=False, verbose=False) -> Optional[list]:
        """
        Run AiderReview on a checked out patch.

        Args:
            change: The change details
            generic_review: Whether to run the generic review
            style_review: Whether to run the style check review
            static_analysis_review: Whether to run the static analysis review
            skip_confirmation: Whether to skip confirmation prompts
            verbose: Whether to print verbose output, including command results

        Returns:
            A list of review comments if successful, None otherwise
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

            # Check if any specific review types were requested
            any_review_requested = generic_review or style_review or static_analysis_review

            # If no specific review types were requested, enable all of them
            if not any_review_requested:
                generic_review = True
                style_review = True
                static_analysis_review = True
                print_green("No specific review types requested. Running all review types.", self)

            # Run the review
            print_green(f"Running review for change {change_number}...", self)
            # The configuration file will be passed to AiderReview, which will handle
            # loading the configuration values and using them as fallbacks for command-line arguments
            review_result = run_review(
                use_paid_model=True,  # Use the paid model for Gerrit reviews
                max_files=None,       # Let AiderReview use the configured value
                max_tokens=None,      # Let AiderReview use the configured value
                output_file=None,     # Don't save to a file
                skip_confirmation=skip_confirmation, # Skip confirmation if requested
                config_file=self.config_file,  # Pass the configuration file
                backend="aider",      # Explicitly specify the backend to use
                generic_review=generic_review,
                style_review=style_review,
                static_analysis_review=static_analysis_review,
                verbose=verbose       # Pass the verbose flag
            )

            if review_result is None:
                print_red("AiderReview did not produce any reviews", self)
                return None

            # Ensure we have a list of responses
            if not isinstance(review_result, list):
                review_result = [review_result]

            if not review_result:  # Check if the list is empty
                print_red("AiderReview produced an empty list of reviews", self)
                return None

            print_green(f"Review completed successfully with {len(review_result)} responses", self)

            # Return the review result (list of responses)
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

    def review_patch(self, change_id: str, skip_gerrit_review: bool = False,
                   generic_review: bool = True, style_review: bool = False,
                   static_analysis_review: bool = False, skip_confirmation: bool = False,
                   patch_version: str = None, verbose: bool = False) -> bool:
        """
        Review a patch from Gerrit.

        This method:
        1. Checks out the patch
        2. Runs AiderReview on it
        3. Posts the review comments back to Gerrit (unless skip_gerrit_review is True)

        Args:
            change_id: The ID of the change to review
            skip_gerrit_review: If True, skip posting the review to Gerrit
            generic_review: Whether to run the generic review
            style_review: Whether to run the style check review
            static_analysis_review: Whether to run the static analysis review
            skip_confirmation: Whether to skip confirmation prompts
            patch_version: The specific patch version to checkout (if None, uses the latest)
            verbose: Whether to print verbose output, including command results

        Returns:
            True if successful, False otherwise
        """
        # Checkout the patch with the specified patch version
        change = self.checkout_patch(change_id, patch_version)
        if not change:
            return False

        # Check if any specific review types were requested
        any_review_requested = generic_review or style_review or static_analysis_review

        # If no specific review types were requested, enable all of them
        if not any_review_requested:
            generic_review = True
            style_review = True
            static_analysis_review = True
            print_green("No specific review types requested. Running all review types.", self)

        # Run AiderReview on the patch with the specified review types
        review_comments = self.run_review_bot(
            change,
            generic_review=generic_review,
            style_review=style_review,
            static_analysis_review=static_analysis_review,
            skip_confirmation=skip_confirmation,
            verbose=verbose
        )

        if not review_comments:
            return False

        # If skip_gerrit_review is True, don't post the review to Gerrit
        if skip_gerrit_review:
            return True

        # Ensure we have a list of responses to process
        if not isinstance(review_comments, list):
            review_comments = [review_comments]

        # Post each review comment separately
        success = True
        for review_comment in review_comments:
            if not self.post_review(change, review_comment):
                success = False
        return success


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
        # Extract the change ID and patch version from the URL if necessary
        change_id, patch_version = GerritClient.extract_change_id_from_url(args.change_id)
        print_green(f"Getting change: {change_id}" + (f" (patch version: {patch_version})" if patch_version else ""))

        # Create a GerritReviewer instance
        reviewer = GerritReviewer(client, config.lustre_dir, args.config)

        # Review the patch
        print_green(f"Reviewing patch {change_id}...")
        success = reviewer.review_patch(
            change_id,
            args.skip_gerrit_review,
            generic_review=args.generic_review,
            style_review=args.style_review,
            static_analysis_review=args.static_analysis_review,
            skip_confirmation=args.yes,
            patch_version=patch_version,
            verbose=args.verbose
        )

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