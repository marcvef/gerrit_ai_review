#!/usr/bin/env python3
"""
Aider Command Output Integration

This script demonstrates how to add command output to the Aider chat context.
It provides utility functions to run shell commands and add their output to the
conversation with the AI assistant.
"""

import os
import sys
from pathlib import Path
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


def main():
    """Main function to run Aider with the Lustre project."""
    # Set the Lustre project directory
    LUSTRE_DIR = "/Users/mvef/git_wip/lustre-release"

    # Verify the directory exists
    if not os.path.isdir(LUSTRE_DIR):
        print(f"Error: Lustre directory not found at {LUSTRE_DIR}")
        print("Please update the LUSTRE_DIR variable with the correct path")
        sys.exit(1)

    # This is a list of files to add to the chat
    fnames = []

    # Set environment variable GEMINI_API_KEY
    # os.environ["GEMINI_API_KEY"] = "AIzaSyCmFZ5jYbIKYwtdfynby_WaGD7FDouyqvc"

    # # Create the model with the API key
    # model = Model("gemini/gemini-2.5-pro-exp-03-25")

    # paid
    os.environ["GEMINI_API_KEY"] = "AIzaSyDwPO_2pjenfvJXLH29-1XkrWjOLanV52I"

    # Create the model with the API key
    model = Model("gemini/gemini-2.5-pro-preview-03-25")

    # Create a GitRepo object pointing to the Lustre directory
    repo = GitRepo(io=None, fnames=fnames, git_dname=LUSTRE_DIR)

    # Create a coder object with the specified repository
    coder = Coder.create(main_model=model, fnames=fnames, repo=repo)

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

    coder.run("Hello how are you? Just want to know whether it works.")

    # Add the current HEAD commit to context
    # add_git_show_to_context(coder)

    # # This will execute one instruction on those files and then return
    # coder.run("You are a professional reviewer and Lustre Engineer. You should check the changes of the commit I just shared with you. You should not under any circumstances attempt to change the files. You are only here to do two tasks: 1. You should provide a summary of the commit, and 2. you should provide a textual visualization showing where the changes were made in the context of the Lustre architecture. For both tasks, be as detailed and specific as possible! The output of git show is already in the context.")

    # # coder.run("Provide me with the Lustre architecture based on the source code you have in the context. Do not ask me do add any files!!!")

    # coder.run("Explain visually where the changes were made in the context of the Lustre architecture. This means visually presenting the Lustre architecture from client to server and highlighting the changes.")

    # Check token usage
    coder.run("/tokens")

    # Additional examples (commented out)
    # coder.run("make it say goodbye")
    # coder.run("/tokens")


if __name__ == "__main__":
    main()
