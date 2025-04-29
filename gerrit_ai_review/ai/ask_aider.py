#!/usr/bin/env python3
"""
AiderReview - Lustre Code Review Assistant

This script provides a class-based implementation of a code review assistant
that uses Aider to analyze git commits in the Lustre codebase and generate
detailed reviews.
"""

import os
import sys
import pathlib
import io
import re
from aider.coders import Coder
from aider.models import Model
from aider.run_cmd import run_cmd
from aider.repo import GitRepo

# Import common utilities and configuration
from gerrit_ai_review.utils.review_common import ReviewConfig, print_green, print_yellow, print_red

class AiderReview:
    """
    A class that encapsulates the functionality for reviewing Lustre code commits
    using Aider and LLM models.
    """

    def __init__(self, args=None, config_file=None):
        """
        Initialize the AiderReview with command line arguments and configuration.

        Args:
            args: Command line arguments (required)
            config_file: Path to configuration file (if None, uses default)
        """
        # Load configuration
        self.config = ReviewConfig(config_file)

        # Validate and set arguments
        if args is None:
            raise ValueError("Arguments must be provided to AiderReview")

        # Validate required arguments
        self._validate_args(args)
        self.args = args

        # Initialize other attributes
        self.coder = None
        self.instruction = None
        self.response = None

        # Register model metadata
        self.register_model_metadata()

    def _validate_args(self, args):
        """
        Validate that the args object has all required attributes.

        Args:
            args: The arguments object to validate

        Raises:
            ValueError: If any required argument is missing
        """
        required_attrs = [
            'yes',           # Skip confirmation prompt
            'output',        # Output file path
            'instruction',   # Instruction file path
            'max_files',     # Maximum number of files to add
            'max_tokens',    # Maximum number of tokens allowed
            'paid_model',    # Whether to use the paid model
            'free_model'     # Whether to use the free model
        ]

        missing_attrs = [attr for attr in required_attrs if not hasattr(args, attr)]
        if missing_attrs:
            raise ValueError(f"Missing required arguments: {', '.join(missing_attrs)}")

    def register_model_metadata(self):
        """Register model metadata from a file to set token limits."""
        from aider.models import register_litellm_models

        # Get the metadata file path from configuration
        metadata_file = self.config.aider_model_metadata_file

        try:
            # Check if the file exists
            if os.path.exists(metadata_file):
                # Register the model metadata
                register_litellm_models([metadata_file])
                print_green(f"Loaded model metadata from: {metadata_file}", self)
            else:
                print_yellow(f"Model metadata file not found: {metadata_file}", self)
                print_yellow("Token limits will use Aider's default values", self)
        except Exception as e:
            print_red(f"Error loading model metadata: {e}", self)

    def setup_free_model(self):
        """Set up the free Gemini model."""
        try:
            # Access the nested dictionary values directly
            api_key = self.config.aider_api_keys["free_gemini"]
            model_name = self.config.aider_models["free_model"]

            if not api_key or not model_name:
                raise ValueError("Missing API key or model name for free model")

            os.environ["GEMINI_API_KEY"] = api_key
            return Model(model_name)
        except (AttributeError, KeyError, ValueError) as e:
            print_yellow(f"Warning: Missing free model configuration: {e}", self)
            print_yellow("Check your config file.", self)
            return None

    def setup_paid_model(self):
        """Set up the paid Gemini model."""
        try:
            # Access the nested dictionary values directly
            api_key = self.config.aider_api_keys["paid_gemini"]
            model_name = self.config.aider_models["paid_model"]

            if not api_key or not model_name:
                raise ValueError("Missing API key or model name for paid model")

            os.environ["GEMINI_API_KEY"] = api_key
            return Model(model_name)
        except (AttributeError, KeyError, ValueError) as e:
            print_yellow(f"Warning: Missing paid model configuration: {e}", self)
            print_yellow("Unable to initialize paid model.", self)
            return None

    def add_ro_refs_to_context(self):
        """Add the common AI reference to the chat context."""
        if self.config.aider_common_ai_refs:
            # Convert relative paths to absolute paths
            absolute_paths = []
            for file_path in self.config.aider_common_ai_refs:
                # Check if the path is already absolute
                if os.path.isabs(file_path):
                    absolute_paths.append(file_path)
                else:
                    # Get the project root directory
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    # Create absolute path
                    abs_path = os.path.abspath(os.path.join(project_root, file_path))
                    absolute_paths.append(abs_path)

            # Join the absolute paths into a space-separated string
            file_list = " ".join(absolute_paths)
            print_green(f"Adding reference files to context: {file_list}", self)
            self.coder.run(f"/read-only {file_list}")

    def setup_environment(self):
        """Set up the Lustre environment and create Aider objects."""
        # Verify the Lustre directory exists
        if not os.path.isdir(self.config.lustre_dir):
            print_red(f"Error: Lustre directory not found at {self.config.lustre_dir}", self)
            print_red("Please update the lustre_dir setting in your configuration file", self)
            sys.exit(1)

        # Initialize the model based on command-line arguments
        if self.args.paid_model:
            print_green("Using paid model as specified by command-line argument", self)
            model = self.setup_paid_model()
        else:
            # Default to free model if not specified or if --free-model is used
            print_green("Using free model" + (" as specified by command-line argument" if self.args.free_model else " (default)"), self)
            model = self.setup_free_model()

        # If the selected model failed to initialize, try the alternative
        if model is None:
            if self.args.paid_model:
                print_green("Paid model initialization failed, falling back to free model", self)
                model = self.setup_free_model()
            elif not self.args.free_model:  # Only try paid model if free model was the default
                print_green("Free model initialization failed, trying paid model", self)
                model = self.setup_paid_model()

        # If we still don't have a valid model, exit
        if model is None:
            print_red("Error: Failed to initialize any model. Please check your configuration.", self)
            sys.exit(1)

        # Create a GitRepo object pointing to the Lustre directory
        repo = GitRepo(io=None, fnames=[], git_dname=self.config.lustre_dir)

        # Create a coder object with the specified repository
        # Use map_tokens from config to control token usage for the repository map
        self.coder = Coder.create(main_model=model, fnames=[], repo=repo, map_tokens=self.config.aider_map_tokens)

        # Add files to the chat context
        self.add_ro_refs_to_context()

        # Print information about the working directory
        print_green(f"Working with Lustre repository at: {self.coder.root}", self)
        print_green(f"Files in chat context: {', '.join(self.coder.get_inchat_relative_files())}", self)
        print_green(f"Using {self.config.aider_map_tokens} tokens for repository map", self)

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
        print_green(f"Running command: {command}", self)
        # Use the repository's root directory for command execution
        _, output = run_cmd(command, cwd=self.coder.root)

        if not output:
            print_yellow("Command produced no output", self)
            return False, ""

        # Format the command output as a message
        formatted_output = f"Output of command `{command}`:\n\n```\n{output}\n```"

        if add_to_context:
            # Add the command output to the chat context
            self.coder.cur_messages += [
                dict(role="user", content=formatted_output),
                dict(role="assistant", content=assistant_response),
            ]
            print_green(f"Added command output to chat context ({len(output.splitlines())} lines)", self)
        else:
            print_green(f"Command output ({len(output.splitlines())} lines) not added to context", self)

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

    def check_and_manage_token_usage(self, max_tokens=200000, added_files=None):
        """
        Check the current token usage and remove files if it exceeds the threshold.

        Args:
            max_tokens (int): Maximum number of tokens allowed
            added_files (list): List of tuples (filename, changes) for files that were added

        Returns:
            bool: True if token usage is within limits, False if files were removed
        """
        if not added_files:
            return True

        # Get the current token usage
        print_green("Checking token usage...", self)

        # Get the current token count from the model
        token_count = self.get_current_token_count()

        if token_count is None:
            print_yellow("Could not determine token usage, keeping all files", self)
            return True

        print_green(f"Current token usage: {token_count:,} tokens", self)

        # If token usage exceeds the threshold, remove files with the least changes
        if token_count > max_tokens:
            print_yellow(f"Token usage exceeds threshold of {max_tokens:,} tokens", self)

            # Sort added files by changes (ascending)
            sorted_files = sorted(added_files, key=lambda x: x[1])

            # Remove files until we're under the threshold or no more files to remove
            files_removed = []
            for filename, changes in sorted_files:
                # Remove the file from context
                try:
                    print_yellow(f"Removing {filename} ({changes} changes) to reduce token usage", self)
                    self.coder.run(f"/drop {filename}")
                    files_removed.append((filename, changes))

                    # Check token usage again
                    new_token_count = self.get_current_token_count()
                    if new_token_count is None or new_token_count <= max_tokens:
                        break
                except Exception as e:
                    print_yellow(f"Could not remove {filename} from context: {e}", self)

            if files_removed:
                print_yellow(f"Removed {len(files_removed)} files to reduce token usage", self)
                new_token_count = self.get_current_token_count()
                if new_token_count is not None:
                    print_green(f"New token usage: {new_token_count:,} tokens", self)
                return False
            else:
                print_yellow("Could not remove any files to reduce token usage", self)
                return False

        return True

    def get_current_token_count(self):
        """
        Get the current token count from the model.

        Returns:
            int: Current token count, or None if it couldn't be determined
        """
        try:
            # Capture the output of the /tokens command
            original_stdout = sys.stdout
            token_output = io.StringIO()
            sys.stdout = token_output

            # Run the /tokens command
            self.coder.run("/tokens")

            # Restore stdout
            sys.stdout = original_stdout

            # Get the output
            output = token_output.getvalue()

            # Parse the output to extract the token count
            # Look for patterns like "$ 0.0000  150,111 tokens total"
            match = re.search(r'\$\s+[\d\.]+\s+([\d,]+)\s+tokens total', output)
            if match:
                # Remove commas and convert to int
                token_count = int(match.group(1).replace(',', ''))
                return token_count

            # Alternative pattern: look for the last line with a token count
            lines = output.strip().split('\n')
            for line in reversed(lines):
                # Look for lines with token counts like "$ 0.0000   75,162 lustre/tests/sanity-sec.sh"
                match = re.search(r'\$\s+[\d\.]+\s+([\d,]+)', line)
                if match:
                    # Remove commas and convert to int
                    token_count = int(match.group(1).replace(',', ''))
                    return token_count

            # Try to extract from the context window information
            # Look for pattern like "49,889 tokens remaining in context window" and "200,000 tokens max context window size"
            remaining_match = re.search(r'([\d,]+)\s+tokens remaining in context window', output)
            max_match = re.search(r'([\d,]+)\s+tokens max context window size', output)

            if remaining_match and max_match:
                remaining_tokens = int(remaining_match.group(1).replace(',', ''))
                max_tokens = int(max_match.group(1).replace(',', ''))
                token_count = max_tokens - remaining_tokens
                return token_count

            return None
        except Exception as e:
            print_yellow(f"Error getting token count: {e}", self)
            return None

    def is_in_ignored_dir(self, filepath):
        """
        Check if a file is in an ignored directory.

        Args:
            filepath (str): Path to the file

        Returns:
            bool: True if the file is in an ignored directory, False otherwise
        """
        # If there are no ignored directories, return False
        if not self.config.aider_ignored_dirs:
            return False

        # Check if the file path starts with any of the ignored directories
        for ignored_dir in self.config.aider_ignored_dirs:
            if filepath.startswith(ignored_dir):
                return True

        return False

    def add_most_changed_files_to_context(self, commit_hash="HEAD", max_files=3):
        """
        Add the files with the most changes from a specific commit to the chat context.

        Args:
            commit_hash (str): The commit hash to analyze, defaults to HEAD
            max_files (int): Maximum number of files to add to context

        Returns:
            list: List of tuples (filename, changes) for files that were added
        """
        print_green(f"Finding the {max_files} most changed files in commit {commit_hash}...", self)

        # Get the list of files changed in the commit with their stats
        cmd = f"git --no-pager diff --numstat {commit_hash}^ {commit_hash}"
        _, output = run_cmd(cmd, cwd=self.coder.root)

        if not output:
            print_yellow(f"No changes found in commit {commit_hash}", self)
            return False

        # Parse the output to get files and their change counts
        # Format: <additions>\t<deletions>\t<filename>
        file_changes = []
        for line in output.strip().split('\n'):
            if not line.strip():
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            try:
                additions = int(parts[0]) if parts[0] != '-' else 0
                deletions = int(parts[1]) if parts[1] != '-' else 0
                filename = parts[2]

                # Skip binary files (marked with - for additions/deletions)
                if additions == 0 and deletions == 0:
                    continue

                total_changes = additions + deletions

                # Check if the file is in an ignored directory
                if self.is_in_ignored_dir(filename):
                    print_yellow(f"Skipping {filename} (in ignored directory)", self)
                    continue

                file_changes.append((filename, total_changes))
            except ValueError:
                continue

        # Sort files by number of changes (descending)
        file_changes.sort(key=lambda x: x[1], reverse=True)

        # Take the top N files
        top_files = file_changes[:max_files]

        if not top_files:
            print_yellow("No text files with changes found in the commit", self)
            return False

        # Add the files to the context
        added_files = []
        for filename, changes in top_files:
            # Try to add the file directly without checking if it exists
            # Aider's /add command will handle the path resolution
            try:
                print_green(f"Attempting to add {filename} to context...", self)

                # Use the file path as reported by git
                self.coder.run(f"/add {filename}")
                added_files.append((filename, changes))

            except Exception as e:
                    print_yellow(f"Could not add {filename} to context: {e}", self)

        # Report what was added
        if added_files:
            print_green("Added the following files to context:", self)
            for filename, changes in added_files:
                print_green(f"  - {filename} ({changes} changes)", self)
            return added_files
        else:
            print_yellow("Could not add any of the changed files to context", self)
            return []

    def read_instruction(self):
        """Read the instruction from the specified file or the default template."""
        # Determine which instruction file to use
        instruction_file = self.args.instruction
        if not instruction_file:
            # The default_instruction_file attribute is guaranteed to exist in ReviewConfig
            instruction_file = self.config.aider_default_instruction_file

        # Read the instruction from the file
        try:
            with open(instruction_file, 'r') as f:
                self.instruction = f.read()
            print_green(f"Using instruction from file: {instruction_file}", self)
        except Exception as e:
            print_red(f"Error reading instruction file {instruction_file}: {e}", self)
            if self.args.instruction:
                print_red("Please provide a valid instruction file using the -i parameter.", self)
            else:
                print_red(f"The default instruction file {instruction_file} was not found.", self)
                print_red("Please create this file or specify a different file using the -i parameter.", self)
            sys.exit(1)

    def save_response_to_file(self):
        """Save the response to the specified file if provided."""
        if not self.response:
            print_yellow("No response to save.", self)
            return

        # Only save if an output file is explicitly specified
        output_file = self.args.output
        if not output_file:
            print_green("No output file specified, response will not be saved to a file.", self)
            return

        # Write the response to the specified file
        try:
            # Create directory if it doesn't exist
            output_path = pathlib.Path(output_file)
            if output_path.parent != pathlib.Path('.'):
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the response to the file
            with open(output_file, "w") as f:
                f.write(self.response)
            print_green(f"Response has been written to {output_file}", self)
        except IOError as e:
            print_red(f"Error writing to file {output_file}: {e}", self)
        except Exception as e:
            print_red(f"Unexpected error creating output file {output_file}: {e}", self)

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
        print_green("Token usage information is displayed above. Please review the cost before proceeding.", self)

        # Check if we should skip confirmation
        if self.args.yes:
            print_green("Skipping confirmation due to --yes flag.", self)
            proceed = True
        else:
            proceed = self.confirm_with_user()

        if not proceed:
            print_yellow("Operation cancelled by user.", self)
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

        # Add the most changed files to context
        added_files = self.add_most_changed_files_to_context(max_files=self.args.max_files)

        # Check token usage and remove files if it exceeds the threshold
        # Note: We're using the configured aider_map_tokens value for the repository map, but still respecting max_tokens for overall context
        self.check_and_manage_token_usage(self.args.max_tokens, added_files)

        # Read the instruction from file
        self.read_instruction()

        # Execute the instruction and save the response
        self.execute_instruction()

        return self.response
