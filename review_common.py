#!/usr/bin/env python3
"""
Common utilities and configuration for ReviewBot and GerritReviewer.
"""

import os
import sys
import yaml

# ANSI color codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


def print_green(message):
    """Print a regular message with a green prefix to distinguish from Aider output."""
    print(f"{GREEN}* [g ♥ a]{RESET} {message}")


def print_yellow(message):
    """Print a warning message with a yellow prefix to distinguish from Aider output."""
    print(f"{YELLOW}* [g ♥ a]{RESET} {message}")


def print_red(message):
    """Print an error message with a red prefix to distinguish from Aider output."""
    print(f"{RED}* [g ♥ a]{RESET} {message}")


class ReviewBotConfig:
    """
    A class that manages configuration for the ReviewBot and Gerrit integration.
    Loads settings from a YAML file with explicit mapping to class attributes.
    """

    # Default configuration file path
    DEFAULT_CONFIG_FILE = "config/config.yaml"

    def __init__(self, config_file=None):
        """
        Initialize the configuration manager with explicit member variables.

        Args:
            config_file: Path to configuration file (if None, uses default)
        """
        # Initialize ReviewBot configuration attributes
        self.lustre_dir = None
        self.default_instruction_file = None
        self.common_ai_refs = None
        self.api_keys = None
        self.models = None
        self.model_metadata_file = None
        self.max_tokens = None
        self.ignored_dirs = None

        # Initialize Gerrit configuration attributes
        self.gerrit_url = None
        self.gerrit_project = None
        self.gerrit_branch = None
        self.gerrit_username = None
        self.gerrit_password = None

        # Set the config file path
        self.config_file = config_file if config_file else self.DEFAULT_CONFIG_FILE

        # Load configuration from file and update members
        self.load_config()

    def load_config(self):
        """
        Load configuration from YAML file and map to explicit class attributes.
        This provides a clear mapping between YAML keys and class members.
        """
        try:
            # Check if the configuration file exists
            if not os.path.exists(self.config_file):
                print_red(f"Configuration file not found: {self.config_file}")
                print_red("Please create a configuration file.")
                sys.exit(1)

            # Load the configuration file
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            print_green(f"Loaded configuration from {self.config_file}")

            # Check if the configuration is empty
            if not config:
                print_red(f"Configuration file is empty: {self.config_file}")
                print_red("Please add the required configuration settings.")
                sys.exit(1)

            # Required configuration fields
            required_fields = [
                'lustre_dir',
                'default_instruction_file',
                'api_keys',
                'models',
                'model_metadata_file',
                'max_tokens',
                'gerrit'
            ]

            # Check for missing required fields
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                print_red(f"Missing required configuration fields: {', '.join(missing_fields)}")
                print_red("Please add these fields to your configuration file.")
                sys.exit(1)

            # Basic settings
            self.lustre_dir = config['lustre_dir']
            self.default_instruction_file = config['default_instruction_file']
            self.model_metadata_file = config['model_metadata_file']
            self.max_tokens = config['max_tokens']

            # List attributes
            self.common_ai_refs = config.get('common_ai_refs', [])
            self.ignored_dirs = config.get('ignored_dirs', [])

            # Nested dictionaries
            self.api_keys = {}
            for key, value in config['api_keys'].items():
                self.api_keys[key] = value

            self.models = {}
            for key, value in config['models'].items():
                self.models[key] = value

            # Check for required nested fields
            if 'free_gemini' not in self.api_keys or 'paid_gemini' not in self.api_keys:
                print_red("Missing required API keys in configuration: free_gemini, paid_gemini")
                print_red("Please add these keys to your configuration file.")
                sys.exit(1)

            if 'free_model' not in self.models or 'paid_model' not in self.models:
                print_red("Missing required model settings in configuration: free_model, paid_model")
                print_red("Please add these settings to your configuration file.")
                sys.exit(1)

            # Load Gerrit configuration
            gerrit_config = config.get('gerrit', {})

            # Required Gerrit fields
            required_gerrit_fields = ['url', 'project', 'branch', 'auth']

            # Check for missing required Gerrit fields
            missing_gerrit_fields = [field for field in required_gerrit_fields if field not in gerrit_config]
            if missing_gerrit_fields:
                print_red(f"Missing required Gerrit configuration fields: {', '.join(missing_gerrit_fields)}")
                print_red("Please add these fields to your configuration file.")
                sys.exit(1)

            # Basic Gerrit settings
            self.gerrit_url = gerrit_config['url']
            self.gerrit_project = gerrit_config['project']
            self.gerrit_branch = gerrit_config['branch']

            # Auth settings
            auth_config = gerrit_config.get('auth', {})
            if 'username' not in auth_config or 'password' not in auth_config:
                print_red("Missing required Gerrit auth fields: username, password")
                print_red("Please add these fields to your configuration file.")
                sys.exit(1)

            self.gerrit_username = auth_config['username']
            self.gerrit_password = auth_config['password']

        except yaml.YAMLError as e:
            print_red(f"Error parsing YAML in configuration file {self.config_file}: {e}")
            sys.exit(1)
        except Exception as e:
            print_red(f"Error loading configuration from {self.config_file}: {e}")
            sys.exit(1)
