#!/usr/bin/env python3
"""
Aider Command Output Integration

This script demonstrates how to add command output to the Aider chat context.
It provides utility functions to run shell commands and add their output to the
conversation with the AI assistant.
"""

import os
import sys
import argparse
from aider.coders import Coder
from aider.models import Model
from aider.run_cmd import run_cmd
from aider.repo import GitRepo

# Function to run a command and add its output to the chat context
def add_command_output_to_context(coder, command, add_to_context=True, assistant_response="I've received the command output and will take it into account."):
    """
    Run a shell command and optionally add its output to the chat context.

    Args:
        coder: The Aider coder object
        command (str): The shell command to execute
        add_to_context (bool): Whether to add the output to the chat context
        assistant_response (str): The response from the assistant to include after the command output

    Returns:
        tuple: (success, output) where success is a boolean indicating if the command produced output
               and output is the command's output as a string
    """
    print(f"Running command: {command}")
    # Use the repository's root directory for command execution
    _, output = run_cmd(command, cwd=coder.root)

    if not output:
        print("Command produced no output")
        return False, ""

    # Format the command output as a message
    formatted_output = f"Output of command `{command}`:\n\n```\n{output}\n```"

    if add_to_context:
        # Add the command output to the chat context
        coder.cur_messages += [
            dict(role="user", content=formatted_output),
            dict(role="assistant", content=assistant_response),
        ]
        print(f"Added command output to chat context ({len(output.splitlines())} lines)")
    else:
        print(f"Command output ({len(output.splitlines())} lines) not added to context")

    return True, output

# Helper function to add git show output to context
def add_git_show_to_context(coder, commit_hash="HEAD"):
    """
    Add the output of git show for a specific commit to the chat context.

    Args:
        coder: The Aider coder object
        commit_hash (str): The commit hash to show, defaults to HEAD

    Returns:
        bool: True if successful, False otherwise
    """
    success, _ = add_command_output_to_context(
        coder,
        f"git --no-pager show {commit_hash}",
        assistant_response="I'll analyze this commit in my response."
    )
    return success

def setup_free():
    os.environ["GEMINI_API_KEY"] = "AIzaSyCmFZ5jYbIKYwtdfynby_WaGD7FDouyqvc"
    return Model("gemini/gemini-2.5-pro-exp-03-25")

def setup_paid():
    os.environ["GEMINI_API_KEY"] = "AIzaSyDwPO_2pjenfvJXLH29-1XkrWjOLanV52I"
    return Model("gemini/gemini-2.5-pro-preview-03-25")

def confirm_with_user():
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

def main():
    """Main function to run Aider with the Lustre project."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run Aider with the Lustre project")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    # Set the Lustre project directory
    LUSTRE_DIR = "/Users/mvef/git_wip/lustre-release"

    # Verify the directory exists
    if not os.path.isdir(LUSTRE_DIR):
        print(f"Error: Lustre directory not found at {LUSTRE_DIR}")
        print("Please update the LUSTRE_DIR variable with the correct path")
        sys.exit(1)

    # This is a list of files to add to the chat
    fnames = ["lustre/ptlrpc/nodemap_handler.c", "lustre/ptlrpc/nodemap_storage.c"]
    # fnames = []

    # model = setup_free()
    model = setup_paid()

    # Create a GitRepo object pointing to the Lustre directory
    repo = GitRepo(io=None, fnames=[], git_dname=LUSTRE_DIR)

    # Create a coder object with the specified repository
    coder = Coder.create(main_model=model, fnames=[]], repo=repo)

    # Print information about the working directory
    print(f"Working with Lustre repository at: {coder.root}")

    # Example usage
    coder.run("/tokens")

    # Add command output to context
    # add_command_output_to_context(coder, "git status")

    # Example of running a command without adding to context
    # success, output = add_command_output_to_context(coder, "ls -la", add_to_context=False)

    # Example with custom assistant response
    # success, _ = add_command_output_to_context(
    #     coder,
    #     "git log -n 3 --oneline",
    #     assistant_response="I'll analyze these recent commits in my response."
    # )

    # coder.run("Hello how are you? Just want to know whether it works.")

    # Add the current HEAD commit to context
    add_git_show_to_context(coder)
    coder.run("/add lustre/ptlrpc/nodemap_handler.c lustre/ptlrpc/nodemap_storage.c")

    # Define the main instruction
    main_instruction = """You are a professional reviewer and Lustre Engineer. You should check the changes of the commit in the context from `git show`. You should not under any circumstances attempt to change the files. You are only here to do two tasks: 1. You should provide a summary of the commit, and 2. you should provide a textual visualization showing where the changes were made in the context of the Lustre architecture which should contain the VFS, client, server, all the way to the back end storage. 3. Critically review the changes and provide useful information for human reviewers to look out for. For all tasks, be as detailed and specific as possible! The output of git show is already in the context."""

    coder.run("/tokens")
    # Show token usage and ask for confirmation if --yes flag is not set
    print("\nToken usage information is displayed above. Please review the cost before proceeding.")

    # Check if we should skip confirmation
    if args.yes:
        print("Skipping confirmation due to --yes flag.")
        proceed = True
    else:
        # Ask for confirmation before proceeding
        proceed = confirm_with_user()

    if proceed:
        # Execute the instruction if confirmed or --yes flag is set
        coder.run(main_instruction)

        # Check final token usage after execution
        coder.run("/tokens")
    else:
        print("Operation cancelled by user.")


if __name__ == "__main__":
    main()
