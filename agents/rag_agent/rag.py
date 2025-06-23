from pymongo import MongoClient
from langchain_community.vectorstores import MongoDBAtlasVectorSearch   # <- Deprecation 경고 반영
from .embedding import KoSBERTEmbeddings 

class RAGSystem:
    def __init__(self):
        # MongoDB 접속 정보 설정
        self.mongo_uri = "mongodb+srv://choi613504:zWqJV1Y4CVF5r4sj@cluster0.jzutl7b.mongodb.net/?retryWrites=true&w=majority&tls=true"
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client["rag_project"]
        self.collection = self.db["documents"]
        
        # KoSBERT 임베딩 및 벡터 검색기 생성
        self.embedding = KoSBERTEmbeddings()
        self.vector_store = MongoDBAtlasVectorSearch(
            collection=self.collection,
            embedding=self.embedding,
            index_name="document_vectors",
            text_key="text",
            embedding_key="embedding"
        )
        
        # Retriever 생성
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 4,  # 검색할 문서의 개수
                "score_threshold": 0.5  # similarity threshold
            }
        )
    
    def search_documents(self, query):
        """
        주어진 쿼리에 대해 관련 문서를 검색합니다.
        
        Args:
            query (str): 검색할 질의
            
        Returns:
            list: 관련 문서 리스트
        """
        relevant_docs = self.retriever.invoke(query)
        return relevant_docs
    
    def close_connection(self):
        """MongoDB 연결을 종료합니다."""
        if self.mongo_client:
            self.mongo_client.close()