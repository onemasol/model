# api/flow_runner.py
from test.test_flow import test_interactive_calendar_flow  # or whatever function
from io import StringIO
import sys

def run_flow_interactive(user_input: str, ocr: str = "") -> str:
    """
    Runs your interactive flow with the given inputs and
    returns only the final answer as a string.
    """
    # Capture stdout to parse out final_answer
    old_stdout, sys.stdout = sys.stdout, StringIO()
    try:
        # You need to adapt this call so that test_interactive_calendar_flow()
        # uses the passed inputs rather than prompting for input().
        # For example, you might refactor test_interactive_calendar_flow()
        # to take arguments instead of reading from stdin.
        result_state = test_interactive_calendar_flow()
        # Assume it returns a dict with "final_answer"
        final = result_state.get("final_answer", "")
    finally:
        sys.stdout = old_stdout
    return final