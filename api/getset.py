"""
getset.py

This module holds globally-shared state for the current session
and user request, so that any part of the API or agent logic can
access the session_id, access_token, user_input, and ocr_result
without circular imports.
"""

# module-level variables for shared state
# None으로 다시 초기화하여 모듈이 로드될 때 상태가 초기화되도록 해야함.
_current_session_id: str | None = "3fa85f64-5717-4562-b3fc-2c963f66afa6" 
_current_access_token: str | None = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA4Nzc4MDQsInN1YiI6IjRhNzI4OTUyLTUzYTAtNGFiZS1hZThjLTBmZjQ0MGQ2NTg1ZSJ9.h9OaG0pmu7xB0CwXHuQU7_v1C5v4bmE21FfU7kenYOA"
_current_user_input: str | None = """
종합
소득세는
소득세법에
따라
개인사업자
또는
기타
종합과세
대상자가
1년
간의
종합소득에
대하여
다음해
5월
1일부터
5월
31일까지
관할
세무서에
신고하여야
하는
조세로서,
동일
기간
내
납부도
병행되어야
함.
2025년의
경우
공휴일로
인하여
6월
2일까지
신고·납부
가능하나,
이를
경과할
시
세액공제·감면의
적용은
원천적으로
배제되며,
가산세
부과
요건이
발생함.
가산세는
무신고납부세액의
20%를
기본으로
적용하며,
납부불성실에
대하여는
미납세액
또는
미달납부세액에
대하여
미납일수
기준
일할계산된
0.022%가
추가
부과되므로
실제
세부담이
크게
가중될
수
있음.
이에
따라
납세자는
각종
증빙서류
의무보관기간을
준수하여
적시
수집하고,
소득공제
및
세액감면
항목을
누락
없이
확인하여야
하며,
장부기장을
요하는
복식부기의무자는
기장불이행
시
추가불이익이
있음을
인지하고,
예정신고,
중간예납,
기장대행,
세무대리인을
통한
위임신고
등
제도적
수단을
사전에
선택·활용하여야
함.
"""
_current_ocr_result: str | None = "일정 추가해줘."

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