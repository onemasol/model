def format_question(question: str) -> str:
    """Format the question into a single line by removing newlines and extra spaces."""
    return " ".join(question.split()) 