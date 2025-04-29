#!/usr/bin/env python3
"""
Common interface for AI integrations.

This script provides a unified interface to different AI backends
(Aider, Augment, etc.) for code review and analysis.
"""

import argparse
import sys

# Import AI integrations
from gerrit_ai_review.ai.ask_aider import AiderReview
from gerrit_ai_review.ai.ask_augment import AugmentReview
from gerrit_ai_review.utils.review_common import print_green, print_yellow, print_red

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run AI-assisted code review with different backends")

    # Common arguments for all backends
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("-o", "--output", type=str,
                       help="Output file to write the response to")
    parser.add_argument("-i", "--instruction", type=str,
                       help="File containing the instruction for the AI")
    parser.add_argument("-c", "--config", type=str,
                       help="Path to configuration file")

    # Backend selection
    backend_group = parser.add_mutually_exclusive_group()
    backend_group.add_argument("--aider", action="store_true", default=True,
                              help="Use Aider as the backend (default)")
    backend_group.add_argument("--augment", action="store_true",
                              help="Use Augment as the backend")

    # Model selection
    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument("-f", "--free-model", action="store_true",
                            help="Use the free model (default)")
    model_group.add_argument("-p", "--paid-model", action="store_true",
                            help="Use the paid model")

    # Other options
    parser.add_argument("--max-files", type=int, default=3,
                       help="Maximum number of most-changed files to add to context (default: 3)")
    parser.add_argument("--max-tokens", type=int, default=200000,
                       help="Maximum number of tokens allowed in context (default: 200,000)")
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

    return parser.parse_args()

def run_review(use_paid_model=False, max_files=3, max_tokens=200000,
              instruction_file=None, output_file=None, skip_confirmation=False,
              backend="aider", config_file=None, generic_review=True, style_review=False,
              static_analysis_review=False, verbose=False):
    """
    Run a review programmatically, without command-line arguments.

    This function is designed to be imported and called from other Python modules,
    such as gerrit_review_patch.py.

    Args:
        use_paid_model (bool): Whether to use the paid model (True) or free model (False)
        max_files (int): Maximum number of files to add to context
        max_tokens (int): Maximum number of tokens allowed in context
        instruction_file (str): Path to the instruction file (if None, uses default)
        output_file (str): Path to save the response (if None, response is not saved to a file)
        skip_confirmation (bool): Whether to skip the confirmation prompt
        backend (str): Which backend to use ("aider" or "augment")
        config_file (str): Path to the configuration file (if None, uses default)
        generic_review (bool): Whether to run the generic review
        style_review (bool): Whether to run the style check review
        static_analysis_review (bool): Whether to run the static analysis review
        verbose (bool): Whether to print verbose output, including command results

    Returns:
        list: A list of responses from the AI model. May be empty if no reviews were generated.
    """
    # Create a simple object to mimic the args namespace
    class Args:
        pass

    args = Args()
    args.paid_model = use_paid_model
    args.free_model = not use_paid_model
    args.max_files = max_files
    args.max_tokens = max_tokens
    args.instruction = instruction_file
    args.output = output_file
    args.yes = skip_confirmation
    args.verbose = verbose

    # AI headers for each review type
    generic_header = "[Gerrit AI Reviewer - Generic Review] This is an AI review and provides a patch summary, visualization, guidance for reviewing. Note that this review is neither necessarily complete nor correct! \n\n"
    style_header = "[Gerrit AI Reviewer - Code Style Review] This is an AI style review and shows potential stylistic issues. Note that this review is neither necessarily complete nor correct! \n\n"
    static_analysis_header = "[Gerrit AI Reviewer - Static Analysis Review] This is an AI static-analysis review and shows potential issues. Note that this review is neither necessarily complete nor correct! \n\n"

    # Select the appropriate backend
    if backend == "aider":
        # Create an AiderReview instance with the args and config file
        bot = AiderReview(args=args, config_file=config_file)

        # Initialize responses list
        responses = []

        # Check if any specific review types were requested
        any_review_requested = generic_review or style_review or static_analysis_review

        # If no specific review types were requested, enable all of them
        if not any_review_requested:
            generic_review = True
            style_review = True
            static_analysis_review = True
            print_green("No specific review types requested. Running all review types.")

        # Run generic review if requested (first)
        if generic_review:
            print_green("Running generic review...")
            generic_response = bot.run_generic()
            if generic_response:
                responses.append(generic_header + generic_response)

        # Run style check if requested (second)
        if style_review:
            print_green("Running style check review...")
            style_check_response = bot.run_style_check()
            if style_check_response:
                responses.append(style_header + style_check_response)

        # Run static analysis if requested (third)
        if static_analysis_review:
            print_green("Running static analysis review...")
            static_analysis_response = bot.run_static_analysis()
            if static_analysis_response:
                responses.append(static_analysis_header + static_analysis_response)

        # Always return a list, even if it contains only one item or is empty
        return responses
    elif backend == "augment":
        # Create an AugmentReview instance with the args and config file
        bot = AugmentReview(args=args, config_file=config_file)
        response = bot.run()

        # Initialize responses list
        responses = []

        if response:
            # Use the generic header for Augment reviews
            responses.append(generic_header + response)

        # Always return a list, even if it's empty
        return responses
    else:
        print_red(f"Unknown backend: {backend}")
        print_red("Error: Invalid backend specified. Please use 'aider' or 'augment'.")
        return []  # Return an empty list for consistency

def run_manual():
    """Main function to run the appropriate AI backend via CLI."""
    args = parse_arguments()

    # Determine which backend to use
    if args.augment:
        print_green("Using Augment backend")
        backend = "augment"
    else:
        print_green("Using Aider backend")
        backend = "aider"

    # Run the review with the selected backend
    run_review(
        use_paid_model=args.paid_model,
        max_files=args.max_files,
        max_tokens=args.max_tokens,
        instruction_file=args.instruction,
        output_file=args.output,
        skip_confirmation=args.yes,
        backend=backend,
        config_file=args.config,
        generic_review=args.generic_review,
        style_review=args.style_review,
        static_analysis_review=args.static_analysis_review,
        verbose=args.verbose
    )