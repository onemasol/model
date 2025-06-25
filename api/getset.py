"""
getset.py

This module holds globally-shared state for the current session
and user request, so that any part of the API or agent logic can
access the session_id, access_token, user_input, and ocr_result
without circular imports.
"""

# module-level variables for shared state
# None으로 다시 초기화하여 모듈이 로드될 때 상태가 초기화되도록 해야함.
_current_session_id: str | None = None
_current_access_token: str | None = None
_current_user_input: str | None = None
_current_ocr_result: str | None = None

def set_current_session_id(session_id: str) -> None:
    """Set the current session ID."""
    global _current_session_id
    _current_session_id = session_id

def get_current_session_id() -> str | None:
    """Get the current session ID."""
    return _current_session_id

def set_current_access_token(token: str) -> None:
    """Set the current access token."""
    global _current_access_token
    _current_access_token = token

def get_current_access_token() -> str | None:
    """Get the current access token."""
    return _current_access_token

def set_current_user_input(user_input: str) -> None:
    """Set the current user input."""
    global _current_user_input
    _current_user_input = user_input

def get_current_user_input() -> str | None:
    """Get the current user input."""
    return _current_user_input

def set_current_ocr_result(ocr_result: str) -> None:
    """Set the current OCR result."""
    global _current_ocr_result
    _current_ocr_result = ocr_result

def get_current_ocr_result() -> str | None:
    """Get the current OCR result."""
    return _current_ocr_result