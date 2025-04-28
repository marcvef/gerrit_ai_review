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
import sys
import urllib.parse
import yaml
from typing import Dict, Any


class GerritConfig:
    """Configuration for Gerrit connection."""

    DEFAULT_CONFIG_FILE = "config/gerrit.yaml"

    def __init__(self, config_file=None):
        """
        Initialize the Gerrit configuration.

        Args:
            config_file: Path to configuration file (if None, uses default)
        """
        # Initialize configuration attributes
        self.url = None
        self.project = None
        self.branch = None
        self.username = None
        self.password = None

        # Set the config file path
        self.config_file = config_file if config_file else self.DEFAULT_CONFIG_FILE

        # Load configuration from file
        self.load_config()

    def load_config(self):
        """
        Load configuration from YAML file.
        """
        try:
            # Check if the configuration file exists
            if not os.path.exists(self.config_file):
                print(f"Configuration file not found: {self.config_file}")
                print("Please create a configuration file.")
                sys.exit(1)

            # Load the configuration file
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            print(f"Loaded Gerrit configuration from {self.config_file}")

            # Check if the configuration is empty
            if not config:
                print(f"Configuration file is empty: {self.config_file}")
                print("Please add the required configuration settings.")
                sys.exit(1)

            # Required configuration fields
            required_fields = [
                'url',
                'project',
                'branch',
                'auth'
            ]

            # Check for missing required fields
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                print(f"Missing required configuration fields: {', '.join(missing_fields)}")
                print("Please add these fields to your configuration file.")
                sys.exit(1)

            # Basic settings
            self.url = config['url']
            self.project = config['project']
            self.branch = config['branch']

            # Auth settings
            if 'username' not in config['auth'] or 'password' not in config['auth']:
                print("Missing required auth fields: username, password")
                print("Please add these fields to your configuration file.")
                sys.exit(1)

            self.username = config['auth']['username']
            self.password = config['auth']['password']

        except yaml.YAMLError as e:
            print(f"Error parsing YAML in configuration file {self.config_file}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading configuration from {self.config_file}: {e}")
            sys.exit(1)


class GerritClient:
    """Client for interacting with Gerrit."""

    def __init__(self, config: GerritConfig):
        """
        Initialize the Gerrit client.

        Args:
            config: Gerrit configuration
        """
        self.config = config
        self.auth = requests.auth.HTTPBasicAuth(config.username, config.password)

    def test_connection(self) -> bool:
        """
        Test the connection to Gerrit.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to get the server version
            path = '/config/server/version'
            response = requests.get(f"{self.config.url}/a{path}", auth=self.auth)

            if response.status_code == 200:
                # Gerrit uses " )]}'" to guard against XSSI
                version = json.loads(response.content[5:])
                print(f"Successfully connected to Gerrit at {self.config.url}")
                print(f"Gerrit version: {version}")
                return True
            else:
                print(f"Failed to connect to Gerrit: {response.status_code} {response.reason}")
                return False
        except Exception as e:
            print(f"Error connecting to Gerrit: {e}")
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
            path = (f"/changes/{urllib.parse.quote(self.config.project, safe='')}~" +
                   f"{urllib.parse.quote(self.config.branch, safe='')}~{change_id}" +
                   "?o=CURRENT_REVISION&o=CURRENT_COMMIT&o=CURRENT_FILES")

        response = requests.get(f"{self.config.url}/a{path}", auth=self.auth)

        if response.status_code != 200:
            print(f"Error getting change: {response.status_code} {response.reason}")
            print(response.text)
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
            return f"git fetch {self.config.url}/a/{self.config.project} refs/changes/{change_number%100:02d}/{change_number}/{current_revision[-8:]} && git checkout FETCH_HEAD"

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
            print("Cannot post review: No change provided")
            return False

        # Get the current revision
        current_revision = change.get('current_revision')
        if not current_revision:
            print("Cannot post review: No current revision found")
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
                f"{self.config.url}/a{path}",
                json=review_input,
                auth=self.auth,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                print("Review posted successfully")
                return True
            else:
                print(f"Error posting review: {response.status_code} {response.reason}")
                print(response.text)
                return False
        except Exception as e:
            print(f"Error posting review: {e}")
            return False


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Connect to Gerrit and review patches")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--test", action="store_true", help="Test the connection to Gerrit")
    parser.add_argument("--change", type=str, help="Specify a change ID or number to retrieve")

    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()

    # Load configuration
    config = GerritConfig(args.config)

    # Create Gerrit client
    client = GerritClient(config)

    # Test connection if requested
    if args.test:
        if client.test_connection():
            print("Connection test successful!")
        else:
            print("Connection test failed!")
        return

    # Get a specific change if requested
    if args.change:
        print(f"Getting change: {args.change}")
        change = client.get_change_by_id(args.change)

        if not change:
            print(f"Change {args.change} not found.")
            return

        # Print change details
        print(f"Change {change['_number']}: {change.get('subject', 'No subject')}")
        print(f"Owner: {change.get('owner', {}).get('name', 'Unknown')}")
        print(f"Project: {change.get('project', 'Unknown')}")
        print(f"Branch: {change.get('branch', 'Unknown')}")
        print(f"Status: {change.get('status', 'Unknown')}")

        # Print current revision details
        current_revision = change.get('current_revision')
        if current_revision:
            revision_info = change.get('revisions', {}).get(current_revision, {})
            print(f"Current revision: {current_revision}")
            print(f"Created: {revision_info.get('created', 'Unknown')}")

            # Get and print the checkout URL
            checkout_url = client.get_checkout_url(change)
            if checkout_url:
                print(f"\nCheckout command:")
                print(f"  {checkout_url}")

            # Print files in the revision
            files = revision_info.get('files', {})
            if files:
                print("\nFiles:")
                for file_path, file_info in files.items():
                    status = file_info.get('status', '?')
                    lines_inserted = file_info.get('lines_inserted', 0)
                    lines_deleted = file_info.get('lines_deleted', 0)
                    print(f"  {status} {file_path} (+{lines_inserted}, -{lines_deleted})")

            # Post a test review comment
            print("\nPosting a test review comment...")
            client.post_review(change)

        return

    # If no action specified, show help
    print("No action specified. Use --test to test the connection or --change to get a specific change.")


if __name__ == "__main__":
    main()