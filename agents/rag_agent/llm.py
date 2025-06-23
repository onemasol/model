from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

class LLMSystem:
    def __init__(self, model_name="exaone3.5:7.8b", temperature=0.5):
        """
        LLM 시스템을 초기화합니다.
        
        Args:
            model_name (str): 사용할 모델명
            temperature (float): 생성 온도 (0.0-1.0)
        """
        self.model = ChatOllama(
            model=model_name,
            temperature=temperature,
        )
        
        # RAG용 프롬프트 템플릿 정의
        self.prompt_template = PromptTemplate(
            template="""다음 문서들을 참고하여 질문에 답변해주세요.

참고 문서:
{context}

질문: {question}

답변: 위 문서들을 참고하여, **반드시 한국어로**, 정확하고 도움 되는 답변을 제공해 주세요. 만약 참고 문서에서 관련 정보를 찾을 수 없다면, 그 사실을 명시해주세요.""",
            input_variables=["context", "question"]
        )
    
    def generate_response(self, query, retrieved_docs):
        """
        검색된 문서를 바탕으로 쿼리에 대한 응답을 생성합니다.
        
        Args:
            query (str): 사용자 질문
            retrieved_docs (list): 검색된 문서 리스트
            
        Returns:
            str: 생성된 응답
        """
        try:
            # 검색된 문서들을 컨텍스트로 결합
            context = self._format_context(retrieved_docs)
            
            # 프롬프트 생성
            prompt = self.prompt_template.format(
                context=context,
                question=query
            )
            
            # LLM에 전달할 메시지 생성
            messages = [HumanMessage(content=prompt)]
            
            # 응답 생성 (최신 방식)
            response = self.model.invoke(messages)
            
            return response.content
            
        except Exception as e:
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _format_context(self, retrieved_docs):
        """
        검색된 문서들을 컨텍스트 형태로 포맷팅합니다.
        
        Args:
            retrieved_docs (list): 검색된 문서 리스트
            
        Returns:
            str: 포맷팅된 컨텍스트
        """
        if not retrieved_docs:
            return "관련 문서를 찾을 수 없습니다."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"[문서 {i}]\n{doc.page_content}")
        
        return "\n\n".join(context_parts)
    
    def generate_simple_response(self, query):
        """
        단순 질문에 대한 응답을 생성합니다 (검색 없이).
        
        Args:
            query (str): 사용자 질문
            
        Returns:
            str: 생성된 응답
        """
        try:
            messages = [HumanMessage(content=query)]
            response = self.model.invoke(messages)
            return response.content
        except Exception as e:
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    def test_connection(self):
        """
        모델 연결을 테스트합니다.
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            test_response = self.generate_simple_response("안녕하세요")
            return "오류가 발생했습니다" not in test_response
        except:
            return False