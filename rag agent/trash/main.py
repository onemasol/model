"""
RAG 기반 법률 문서 챗봇 메인 실행 모듈
PDF 파싱 -> 청킹 -> 임베딩 -> 벡터 DB 저장 파이프라인
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

from parsing import parse_pdf_file, PageData
from chunking import chunk_legal_document, Chunk

# # 로깅 설정
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

class LegalRAGSystem:
    """법률 문서 RAG 시스템"""
    
    def __init__(self, db_path: str = "legal_rag.db", model_name: str = "jhgan/ko-sroberta-multitask"):
        self.db_path = db_path
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = 768  # ko-sroberta-multitask 기본 차원
        self._init_database()
        logger.info(f"RAG 시스템 초기화 완료: {model_name}")
    
    def _init_database(self):
        """벡터 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 문서 정보 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT,
                file_path TEXT,
                total_pages INTEGER,
                total_chunks INTEGER,
                created_at TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # 청크 정보 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                text TEXT,
                chunk_type TEXT,
                hierarchy_level INTEGER,
                page_nums TEXT,
                parent_chunk_id TEXT,
                embedding BLOB,
                metadata TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        # 검색 성능을 위한 인덱스
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunk_type ON chunks (chunk_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hierarchy ON chunks (hierarchy_level)')
        
        conn.commit()
        conn.close()
        logger.info("데이터베이스 초기화 완료")
    
    def process_pdf_document(self, pdf_path: str, max_chunk_size: int = 1000) -> str:
        """PDF 문서 전체 처리 파이프라인"""
        logger.info(f"PDF 처리 시작: {pdf_path}")
        
        # 1. PDF 파싱
        try:
            pages_data, doc_metadata = parse_pdf_file(pdf_path)
            logger.info(f"파싱 완료: {len(pages_data)}개 페이지")
        except Exception as e:
            logger.error(f"PDF 파싱 실패: {e}")
            raise
        
        # 2. 계층적 청킹
        try:
            chunks, chunk_summary = chunk_legal_document(pages_data, max_chunk_size)
            logger.info(f"청킹 완료: {len(chunks)}개 청크")
        except Exception as e:
            logger.error(f"청킹 실패: {e}")
            raise
        
        # 3. 임베딩 생성
        try:
            embeddings = self._create_embeddings(chunks)
            logger.info(f"임베딩 생성 완료: {len(embeddings)}개")
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise
        
        # 4. 데이터베이스 저장
        try:
            document_id = self._save_to_database(
                pdf_path, pages_data, doc_metadata, chunks, chunk_summary, embeddings
            )
            logger.info(f"데이터베이스 저장 완료: {document_id}")
            return document_id
        except Exception as e:
            logger.error(f"데이터베이스 저장 실패: {e}")
            raise
    
    def _create_embeddings(self, chunks: List[Chunk]) -> List[np.ndarray]:
        """청크 리스트를 임베딩으로 변환"""
        texts = [chunk.text for chunk in chunks]
        
        # 배치 처리로 임베딩 생성
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch_texts, 
                convert_to_numpy=True,
                show_progress_bar=True
            )
            embeddings.extend(batch_embeddings)
            
            if i % (batch_size * 10) == 0:
                logger.info(f"임베딩 진행률: {i}/{len(texts)}")
        
        return embeddings
    
    def _save_to_database(self, pdf_path: str, pages_data: List[PageData], 
                         doc_metadata: Dict, chunks: List[Chunk], 
                         chunk_summary: Dict, embeddings: List[np.ndarray]) -> str:
        """데이터베이스에 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 문서 ID 생성
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 문서 정보 저장
            cursor.execute('''
                INSERT INTO documents (id, title, file_path, total_pages, total_chunks, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                doc_metadata['document_title'],
                pdf_path,
                doc_metadata['total_pages'],
                len(chunks),
                datetime.now(),
                json.dumps({**doc_metadata, **chunk_summary}, ensure_ascii=False)
            ))
            
            # 청크 정보 저장
            for chunk, embedding in zip(chunks, embeddings):
                cursor.execute('''
                    INSERT INTO chunks (id, document_id, text, chunk_type, hierarchy_level, 
                                      page_nums, parent_chunk_id, embedding, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chunk.id,
                    document_id,
                    chunk.text,
                    chunk.chunk_type,
                    chunk.hierarchy_level,
                    json.dumps(chunk.page_nums),
                    chunk.parent_chunk_id,
                    embedding.tobytes(),  # numpy array를 bytes로 저장
                    json.dumps(chunk.metadata, ensure_ascii=False),
                    datetime.now()
                ))
            
            conn.commit()
            logger.info(f"데이터베이스 저장 완료: {document_id}")
            return document_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"데이터베이스 저장 중 오류: {e}")
            raise
        finally:
            conn.close()
    
    def search_similar_chunks(self, query: str, top_k: int = 5, 
                            chunk_type_filter: Optional[str] = None) -> List[Dict]:
        """유사 청크 검색"""
        # 쿼리 임베딩
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 필터 조건 설정
        where_clause = ""
        params = []
        if chunk_type_filter:
            where_clause = "WHERE chunk_type = ?"
            params.append(chunk_type_filter)
        
        # 모든 청크 조회
        cursor.execute(f'''
            SELECT id, text, chunk_type, hierarchy_level, page_nums, embedding, metadata
            FROM chunks {where_clause}
            ORDER BY created_at DESC
        ''', params)
        
        results = []
        for row in cursor.fetchall():
            chunk_id, text, chunk_type, hierarchy_level, page_nums, embedding_bytes, metadata = row
            
            # 임베딩 복원
            chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            # 코사인 유사도 계산
            similarity = np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )
            
            results.append({
                'chunk_id': chunk_id,
                'text': text,
                'chunk_type': chunk_type,
                'hierarchy_level': hierarchy_level,
                'page_nums': json.loads(page_nums),
                'metadata': json.loads(metadata),
                'similarity': float(similarity)
            })
        
        conn.close()
        
        # 유사도 순으로 정렬하여 상위 k개 반환
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def get_document_list(self) -> List[Dict]:
        """저장된 문서 리스트 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, file_path, total_pages, total_chunks, created_at
            FROM documents
            ORDER BY created_at DESC
        ''')
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'id': row[0],
                'title': row[1],
                'file_path': row[2],
                'total_pages': row[3],
                'total_chunks': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        return documents
    
    def get_chunk_statistics(self) -> Dict:
        """청크 통계 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 전체 통계
        cursor.execute('SELECT COUNT(*) FROM chunks')
        total_chunks = cursor.fetchone()[0]
        
        # 타입별 통계
        cursor.execute('''
            SELECT chunk_type, COUNT(*) 
            FROM chunks 
            GROUP BY chunk_type
            ORDER BY COUNT(*) DESC
        ''')
        type_stats = dict(cursor.fetchall())
        
        # 계층별 통계
        cursor.execute('''
            SELECT hierarchy_level, COUNT(*) 
            FROM chunks 
            GROUP BY hierarchy_level
            ORDER BY hierarchy_level
        ''')
        hierarchy_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_chunks': total_chunks,
            'chunk_types': type_stats,
            'hierarchy_levels': hierarchy_stats
        }

def main():
    # """메인 실행 함수"""
    # # RAG 시스템 초기화
    rag_system = LegalRAGSystem()
    
    # 테스트 PDF 경로
    test_pdf_path = "C:/rag agent/pdf_data/[별표 14] 업종별시설기준(제36조 관련).pdf"
    
    # if not os.path.exists(test_pdf_path):
    #     logger.error(f"PDF 파일을 찾을 수 없습니다: {test_pdf_path}")
    #     return
    
    try:
        # PDF 처리
        document_id = rag_system.process_pdf_document(test_pdf_path, max_chunk_size=800)
        
        # 결과 확인
        print(f"\n=== 처리 완료 ===")
        print(f"문서 ID: {document_id}")
        
        # 통계 출력
        stats = rag_system.get_chunk_statistics()
        print(f"\n=== 청킹 통계 ===")
        print(f"총 청크 수: {stats['total_chunks']}")
        print(f"청크 타입별: {stats['chunk_types']}")
        print(f"계층별: {stats['hierarchy_levels']}")
        
    #     # 검색 테스트
    #     print(f"\n=== 검색 테스트 ===")
    #     test_queries = ["시설기준", "업종별", "별표"]
        
    #     for query in test_queries:
    #         results = rag_system.search_similar_chunks(query, top_k=3)
    #         print(f"\n쿼리: '{query}'")
    #         for i, result in enumerate(results, 1):
    #             print(f"{i}. 유사도: {result['similarity']:.3f}")
    #             print(f"   타입: {result['chunk_type']}, 페이지: {result['page_nums']}")
    #             print(f"   내용: {result['text'][:100]}...")
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()