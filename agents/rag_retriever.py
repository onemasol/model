# agents/rag_retriever.py

from agents.rag_agent.rag import RAGSystem
from agents.rag_agent.llm import LLMSystem

# 객체는 보통 모듈 로딩 시 1회만 생성 (재사용/성능 위해)
rag_system = RAGSystem()
llm_system = LLMSystem()

def rag_retriever(state: dict) -> dict:
    """
    state["messages"][-1]에 있는 최신 사용자 쿼리를 받아
    1. RAG 문서 검색 → 문서 기반 답변 생성
    2. 결과를 state["rag_result"], state["rag_docs"]에 저장
    3. agent_messages 로그 기록
    4. next_node는 지정하지 않음 (분기는 라우터에서)
    """

    user_query = state["messages"][-1]

    # 1. 문서 검색 (RAG)
    relevant_docs = rag_system.search_documents(user_query)

    # 2. 답변 생성
    if relevant_docs:
        answer = llm_system.generate_response(user_query, relevant_docs)
        doc_summary = "\n\n".join([getattr(doc, "page_content", str(doc)) for doc in relevant_docs])
        state["rag_docs"] = doc_summary[:2000]   # 길면 일부만
    else:
        answer = llm_system.generate_simple_response(user_query)
        state["rag_docs"] = "관련 문서 없음"

    state["rag_result"] = answer

    # 3. agent_messages 로그 기록
    state.setdefault("agent_messages", []).append({
        "agent": "rag_retriever",
        "user_query": user_query,
        "doc_count": len(relevant_docs),
        "rag_result": answer,
        "docs_snippet": state["rag_docs"][:300] if "rag_docs" in state else ""
    })

    # 4. 다음 분기는 외부 라우터(critic 등)에서 결정
    return state
