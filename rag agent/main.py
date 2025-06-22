from rag import RAGSystem
from llm import LLMSystem

def main():
    # RAG 시스템과 LLM 시스템 초기화
    rag_system = RAGSystem()
    llm_system = LLMSystem()
    
    print("RAG 기반 질의응답 시스템이 시작되었습니다.")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
    
    try:
        while True:
            # 사용자로부터 쿼리 입력 받기
            query = input("질문을 입력하세요: ").strip()
            
            # 종료 조건 확인
            if query.lower() in ['quit', 'exit', '종료']:
                print("시스템을 종료합니다.")
                break
            
            if not query:
                print("질문을 입력해주세요.")
                continue
            
            print(f"\n🔍 '{query}' 검색 중...")
            
            # 질의 실행 (문서 검색)
            relevant_docs = rag_system.search_documents(query)
            
            # LLM을 통한 답변 생성
            print("💭 답변 생성 중...")
            response = llm_system.generate_response(query, relevant_docs)
            
            # 결과 출력
            print("\n" + "=" * 60)
            print("📋 최종 답변:")
            print("=" * 60)
            print(response)
            
            # 참고 문서 정보 출력 (선택사항)
            # if relevant_docs:
            #     print(f"\n📚 참고된 문서 ({len(relevant_docs)}개):")
            #     print("-" * 40)
            #     for i, doc in enumerate(relevant_docs, 1):
            #         print(f"[문서 {i}] {doc.page_content[:100]}...")
            #         if doc.metadata:
            #             print(f"메타데이터: {doc.metadata}")
            #         print()
            # else:
            #     print("\n⚠️  관련 문서를 찾을 수 없어 일반적인 답변을 제공했습니다.")
            
            print("\n" + "=" * 60 + "\n")
            
    except KeyboardInterrupt:
        print("\n\n시스템을 종료합니다.")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
    
    finally:
        # MongoDB 연결 종료
        rag_system.close_connection()
        print("시스템이 정상적으로 종료되었습니다.")

if __name__ == "__main__":
    main()