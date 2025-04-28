#!/usr/bin/env python3
"""
ReviewBot - Lustre Code Review Assistant

This script provides a class-based implementation of a code review assistant
that uses Aider to analyze git commits in the Lustre codebase and generate
detailed reviews.
"""

import os
import sys
import argparse
import pathlib
import yaml
from aider.coders import Coder
from aider.models import Model
from aider.run_cmd import run_cmd
from aider.repo import GitRepo


class ReviewBotConfig:
    """
    A class that manages configuration for the ReviewBot.
    Loads settings from a YAML file with explicit mapping to class attributes.
    """

    # Default configuration file path
    DEFAULT_CONFIG_FILE = "config/common.yaml"

    def __init__(self, config_file=None):
        """
        Initialize the configuration manager with explicit member variables.

        Args:
            config_file: Path to configuration file (if None, uses default)
        """
        # Default values for all configuration parameters
        self.lustre_dir = "/Users/mvef/git_wip/lustre-release"
        self.default_output_file = "aider_response.txt"
        self.default_instruction_file = "config/default_instruction.txt"
        self.default_files = [
            "lustre/ptlrpc/nodemap_handler.c",
            "lustre/ptlrpc/nodemap_storage.c"
        ]

        # API keys with nested structure
        self.api_keys = {
            "free_gemini": "AIzaSyCmFZ5jYbIKYwtdfynby_WaGD7FDouyqvc",
            "paid_gemini": "AIzaSyDwPO_2pjenfvJXLH29-1XkrWjOLanV52I"
        }

        # Model settings with nested structure
        self.models = {
            "free_model": "gemini/gemini-2.5-pro-exp-03-25",
            "paid_model": "gemini/gemini-2.5-pro-preview-03-25"
        }

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
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            print(f"Loaded configuration from {self.config_file}")

            # Explicitly map YAML keys to class attributes
            if config:
                # Basic settings
                if 'lustre_dir' in config:
                    self.lustre_dir = config['lustre_dir']
                if 'default_output_file' in config:
                    self.default_output_file = config['default_output_file']
                if 'default_instruction_file' in config:
                    self.default_instruction_file = config['default_instruction_file']
                if 'default_files' in config:
                    self.default_files = config['default_files']

                # Nested settings
                if 'api_keys' in config:
                    for key, value in config['api_keys'].items():
                        self.api_keys[key] = value

                if 'models' in config:
                    for key, value in config['models'].items():
                        self.models[key] = value

        except Exception as e:
            print(f"Error loading configuration from {self.config_file}: {e}")
            print("Using default configuration values")


class ReviewBot:
    """
    A class that encapsulates the functionality for reviewing Lustre code commits
    using Aider and LLM models.
    """

    def __init__(self, args=None, config_file=None):
        """
        Initialize the ReviewBot with command line arguments and configuration.

        Args:
            args: Command line arguments (if None, they will be parsed)
            config_file: Path to configuration file (if None, uses default)
        """
        # Load configuration
        self.config = ReviewBotConfig(config_file)

        # Parse arguments
        self.args = args if args is not None else self.parse_arguments()

        # Initialize other attributes
        self.coder = None
        self.instruction = None
        self.response = None

    def parse_arguments(self):
        """Parse command-line arguments."""
        default_output = self.config.default_output_file
        default_instruction = self.config.default_instruction_file

        parser = argparse.ArgumentParser(description="Run Aider with the Lustre project")
        parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
        parser.add_argument("-o", "--output", type=str,
                           help=f"Output file to write the response to (default: {default_output})")
        parser.add_argument("-i", "--instruction", type=str,
                           help=f"File containing the instruction for Aider (default: {default_instruction})")

        # Add model selection arguments in a mutually exclusive group
        model_group = parser.add_mutually_exclusive_group()
        model_group.add_argument("-f", "--free-model", action="store_true",
                                help="Use the free model (default)")
        model_group.add_argument("-p", "--paid-model", action="store_true",
                                help="Use the paid model")

        return parser.parse_args()

    def setup_free_model(self):
        """Set up the free Gemini model."""
        try:
            # Access the nested dictionary values directly
            api_key = self.config.api_keys["free_gemini"]
            model_name = self.config.models["free_model"]

            if not api_key or not model_name:
                raise ValueError("Missing API key or model name for free model")

            os.environ["GEMINI_API_KEY"] = api_key
            return Model(model_name)
        except (AttributeError, KeyError, ValueError) as e:
            print(f"Warning: Missing free model configuration: {e}")
            print("Check your config file.")
            return None

    def setup_paid_model(self):
        """Set up the paid Gemini model."""
        try:
            # Access the nested dictionary values directly
            api_key = self.config.api_keys["paid_gemini"]
            model_name = self.config.models["paid_model"]

            if not api_key or not model_name:
                raise ValueError("Missing API key or model name for paid model")

            os.environ["GEMINI_API_KEY"] = api_key
            return Model(model_name)
        except (AttributeError, KeyError, ValueError) as e:
            print(f"Warning: Missing paid model configuration: {e}")
            print("Unable to initialize paid model.")
            return None

    def add_files_to_context(self):
        """Add the default files to the chat context."""
        # The default_files attribute is guaranteed to exist in ReviewBotConfig
        if self.config.default_files:
            file_list = " ".join(self.config.default_files)
            self.coder.run(f"/add {file_list}")
        else:
            print("Warning: No default files specified in configuration")

    def setup_environment(self):
        """Set up the Lustre environment and create Aider objects."""
        # Verify the Lustre directory exists
        if not os.path.isdir(self.config.lustre_dir):
            print(f"Error: Lustre directory not found at {self.config.lustre_dir}")
            print("Please update the lustre_dir setting in your configuration file")
            sys.exit(1)

        # Initialize the model based on command-line arguments
        if self.args.paid_model:
            print("Using paid model as specified by command-line argument")
            model = self.setup_paid_model()
        else:
            # Default to free model if not specified or if --free-model is used
            print("Using free model" + (" as specified by command-line argument" if self.args.free_model else " (default)"))
            model = self.setup_free_model()

        # If the selected model failed to initialize, try the alternative
        if model is None:
            if self.args.paid_model:
                print("Paid model initialization failed, falling back to free model")
                model = self.setup_free_model()
            elif not self.args.free_model:  # Only try paid model if free model was the default
                print("Free model initialization failed, trying paid model")
                model = self.setup_paid_model()

        # If we still don't have a valid model, exit
        if model is None:
            print("Error: Failed to initialize any model. Please check your configuration.")
            sys.exit(1)

        # Create a GitRepo object pointing to the Lustre directory
        repo = GitRepo(io=None, fnames=[], git_dname=self.config.lustre_dir)

        # Create a coder object with the specified repository
        self.coder = Coder.create(main_model=model, fnames=[], repo=repo)

        # Add files to the chat context
        self.add_files_to_context()

        # Print information about the working directory
        print(f"Working with Lustre repository at: {self.coder.root}")
        print(f"Files in chat context: {', '.join(self.coder.get_inchat_relative_files())}")

        # Show initial token usage
        self.coder.run("/tokens")



    def add_command_output_to_context(self, command, add_to_context=True,
                                     assistant_response="I've received the command output and will take it into account."):
        """
        Run a shell command and optionally add its output to the chat context.

        Args:
            command (str): The shell command to execute
            add_to_context (bool): Whether to add the output to the chat context
            assistant_response (str): The response from the assistant to include after the command output

        Returns:
            tuple: (success, output) where success is a boolean indicating if the command produced output
                  and output is the command's output as a string
        """
        print(f"Running command: {command}")
        # Use the repository's root directory for command execution
        _, output = run_cmd(command, cwd=self.coder.root)

        if not output:
            print("Command produced no output")
            return False, ""

        # Format the command output as a message
        formatted_output = f"Output of command `{command}`:\n\n```\n{output}\n```"

        if add_to_context:
            # Add the command output to the chat context
            self.coder.cur_messages += [
                dict(role="user", content=formatted_output),
                dict(role="assistant", content=assistant_response),
            ]
            print(f"Added command output to chat context ({len(output.splitlines())} lines)")
        else:
            print(f"Command output ({len(output.splitlines())} lines) not added to context")

        return True, output

    def add_git_show_to_context(self, commit_hash="HEAD"):
        """
        Add the output of git show for a specific commit to the chat context.

        Args:
            commit_hash (str): The commit hash to show, defaults to HEAD

        Returns:
            bool: True if successful, False otherwise
        """
        success, _ = self.add_command_output_to_context(
            f"git --no-pager show {commit_hash}",
            assistant_response="I'll analyze this commit in my response."
        )
        return success

    def read_instruction(self):
        """Read the instruction from the specified file or the default template."""
        # Determine which instruction file to use
        instruction_file = self.args.instruction
        if not instruction_file:
            # The default_instruction_file attribute is guaranteed to exist in ReviewBotConfig
            instruction_file = self.config.default_instruction_file

        # Read the instruction from the file
        try:
            with open(instruction_file, 'r') as f:
                self.instruction = f.read()
            print(f"Using instruction from file: {instruction_file}")
        except Exception as e:
            print(f"Error reading instruction file {instruction_file}: {e}")
            if self.args.instruction:
                print("Please provide a valid instruction file using the -i parameter.")
            else:
                print(f"The default instruction file {instruction_file} was not found.")
                print("Please create this file or specify a different file using the -i parameter.")
            sys.exit(1)

    def save_response_to_file(self):
        """Save the response to the specified file or a default file."""
        if not self.response:
            print("No response to save.")
            return

        # Determine the output file path
        output_file = self.args.output
        if not output_file:
            # The default_output_file attribute is guaranteed to exist in ReviewBotConfig
            output_file = self.config.default_output_file

        # Write the response to the specified file
        try:
            # Create directory if it doesn't exist
            output_path = pathlib.Path(output_file)
            if output_path.parent != pathlib.Path('.'):
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the response to the file
            with open(output_file, "w") as f:
                f.write(self.response)
            print(f"\nResponse has been written to {output_file}")
        except IOError as e:
            print(f"\nError writing to file {output_file}: {e}")
        except Exception as e:
            print(f"\nUnexpected error creating output file {output_file}: {e}")

    def confirm_with_user(self):
        """
        Ask the user for confirmation before proceeding with the operation.

        Returns:
            bool: True if the user confirms, False otherwise
        """
        # Ask for confirmation
        while True:
            response = input("\nDo you want to proceed with this request? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'.")

    def execute_instruction(self):
        """Execute the instruction and save the response to a file."""
        # Show token usage and ask for confirmation
        self.coder.run("/tokens")
        print("\nToken usage information is displayed above. Please review the cost before proceeding.")

        # Check if we should skip confirmation
        if self.args.yes:
            print("Skipping confirmation due to --yes flag.")
            proceed = True
        else:
            proceed = self.confirm_with_user()

        if not proceed:
            print("Operation cancelled by user.")
            return

        # Execute the instruction
        self.response = self.coder.run(self.instruction)

        # Save the response to a file
        self.save_response_to_file()

        # Show final token usage
        self.coder.run("/tokens")

    def run(self):
        """Run the complete review process."""
        # Set up the environment
        self.setup_environment()

        # Add git show output to context
        self.add_git_show_to_context()

        # Read the instruction from file
        self.read_instruction()

        # Execute the instruction and save the response
        self.execute_instruction()


def main():
    """Main function to run the ReviewBot."""
    bot = ReviewBot()
    bot.run()


if __name__ == "__main__":
    main()
