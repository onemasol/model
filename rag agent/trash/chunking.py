"""
계층적 구조 기반 청킹 모듈
법률 문서의 구조를 분석하여 의미 단위로 청킹
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from parsing import PageData
import logging

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    """청크 데이터 클래스"""
    id: str
    text: str
    chunk_type: str
    hierarchy_level: int
    metadata: Dict
    page_nums: List[int]
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = None

class HierarchicalChunker:
    """계층적 구조 기반 청킹 클래스"""
    
    def __init__(self, max_chunk_size: int = 1000, overlap_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.chunk_counter = 0
        
        # 청킹 우선순위 (높은 번호가 우선)
        self.hierarchy_patterns = {
            'law_article': {'pattern': re.compile(r'제\s*(\d+)\s*조\s*(?:\(([^)]+)\))?'), 'level': 1},
            'paragraph': {'pattern': re.compile(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]'), 'level': 2},
            'item': {'pattern': re.compile(r'[가-힣]\.\s'), 'level': 3},
            'table_section': {'pattern': re.compile(r'\[별표\s*(\d+)\]'), 'level': 1},
            'chapter': {'pattern': re.compile(r'제\s*(\d+)\s*장\s*([^\n\r]+)'), 'level': 0},
            'section': {'pattern': re.compile(r'제\s*(\d+)\s*절\s*([^\n\r]+)'), 'level': 0}
        }
    
    def chunk_pages(self, pages_data: List[PageData]) -> List[Chunk]:
        """페이지 데이터를 계층적으로 청킹"""
        chunks = []
        
        # 1단계: 구조 기반 청킹
        structural_chunks = self._create_structural_chunks(pages_data)
        chunks.extend(structural_chunks)
        
        # 2단계: 큰 청크에 대해 추가 분할
        refined_chunks = self._refine_large_chunks(chunks)
        
        # 3단계: 메타데이터 보강
        final_chunks = self._enrich_metadata(refined_chunks, pages_data)
        
        logger.info(f"총 {len(final_chunks)}개 청크 생성 완료")
        return final_chunks
    
    def _create_structural_chunks(self, pages_data: List[PageData]) -> List[Chunk]:
        """구조적 요소 기반 청크 생성"""
        chunks = []
        current_text = ""
        current_pages = []
        current_structure = None
        
        for page_data in pages_data:
            if page_data.structure_type == 'law_articles':
                # 조문별로 청킹
                article_chunks = self._chunk_by_articles(page_data)
                chunks.extend(article_chunks)
                
            elif page_data.structure_type == 'table_format':
                # 별표는 독립적인 청크로 처리
                table_chunk = self._create_table_chunk(page_data)
                chunks.append(table_chunk)
                
            elif page_data.structure_type == 'structural':
                # 장/절 단위로 청킹
                if current_structure != page_data.structure_type:
                    if current_text:
                        chunk = self._create_chunk(current_text, 'structural', 0, current_pages)
                        chunks.append(chunk)
                    current_text = page_data.text
                    current_pages = [page_data.page_num]
                    current_structure = page_data.structure_type
                else:
                    current_text += f"\n{page_data.text}"
                    current_pages.append(page_data.page_num)
                    
            else:
                # 일반 텍스트는 연속성 기준으로 청킹
                current_text += f"\n{page_data.text}"
                current_pages.append(page_data.page_num)
                
                if len(current_text) > self.max_chunk_size:
                    chunk = self._create_chunk(current_text, 'plain_text', 3, current_pages)
                    chunks.append(chunk)
                    current_text = ""
                    current_pages = []
        
        # 남은 텍스트 처리
        if current_text.strip():
            chunk = self._create_chunk(current_text, current_structure or 'plain_text', 3, current_pages)
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_articles(self, page_data: PageData) -> List[Chunk]:
        """조문별 청킹"""
        chunks = []
        text = page_data.text
        
        # 조문 위치 찾기
        article_pattern = self.hierarchy_patterns['law_article']['pattern']
        matches = list(article_pattern.finditer(text))
        
        if not matches:
            # 조문이 없으면 전체를 하나의 청크로
            chunk = self._create_chunk(
                text, 'law_article', 1, [page_data.page_num],
                metadata={'article_type': 'general'}
            )
            chunks.append(chunk)
            return chunks
        
        # 조문별로 분할
        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            
            article_text = text[start_pos:end_pos].strip()
            article_num = match.group(1)
            article_title = match.group(2) if match.group(2) else ""
            
            # 조문 내 항 단위로 추가 분할
            paragraph_chunks = self._chunk_by_paragraphs(
                article_text, article_num, article_title, page_data.page_num
            )
            chunks.extend(paragraph_chunks)
        
        return chunks
    
    def _chunk_by_paragraphs(self, article_text: str, article_num: str, 
                           article_title: str, page_num: int) -> List[Chunk]:
        """조문 내 항별 청킹"""
        chunks = []
        paragraph_pattern = self.hierarchy_patterns['paragraph']['pattern']
        matches = list(paragraph_pattern.finditer(article_text))
        
        if not matches or len(article_text) <= self.max_chunk_size:
            # 항이 없거나 충분히 작으면 전체를 하나의 청크로
            chunk = self._create_chunk(
                article_text, 'law_article', 1, [page_num],
                metadata={'article_num': article_num, 'article_title': article_title}
            )
            chunks.append(chunk)
            return chunks
        
        # 항별로 분할
        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(article_text)
            
            paragraph_text = article_text[start_pos:end_pos].strip()
            paragraph_symbol = match.group()
            
            chunk = self._create_chunk(
                paragraph_text, 'paragraph', 2, [page_num],
                metadata={
                    'article_num': article_num,
                    'article_title': article_title,
                    'paragraph_symbol': paragraph_symbol
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_table_chunk(self, page_data: PageData) -> Chunk:
        """별표 청크 생성"""
        table_nums = re.findall(r'\[별표\s*(\d+)\]', page_data.text)
        table_num = table_nums[0] if table_nums else "unknown"
        
        return self._create_chunk(
            page_data.text, 'table_format', 1, [page_data.page_num],
            metadata={'table_num': table_num, 'table_type': 'appendix'}
        )
    
    def _create_chunk(self, text: str, chunk_type: str, hierarchy_level: int, 
                     page_nums: List[int], metadata: Dict = None) -> Chunk:
        """청크 생성 헬퍼 함수"""
        self.chunk_counter += 1
        chunk_id = f"chunk_{self.chunk_counter:04d}"
        
        if metadata is None:
            metadata = {}
        
        metadata.update({
            'text_length': len(text),
            'word_count': len(text.split()),
            'creation_order': self.chunk_counter
        })
        
        return Chunk(
            id=chunk_id,
            text=text.strip(),
            chunk_type=chunk_type,
            hierarchy_level=hierarchy_level,
            metadata=metadata,
            page_nums=page_nums,
            child_chunk_ids=[]
        )
    
    def _refine_large_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """큰 청크를 추가 분할"""
        refined_chunks = []
        
        for chunk in chunks:
            if len(chunk.text) <= self.max_chunk_size:
                refined_chunks.append(chunk)
            else:
                # 큰 청크를 문장 단위로 분할
                sub_chunks = self._split_large_chunk(chunk)
                refined_chunks.extend(sub_chunks)
        
        return refined_chunks
    
    def _split_large_chunk(self, chunk: Chunk) -> List[Chunk]:
        """큰 청크를 문장 단위로 분할"""
        sentences = re.split(r'[.!?]\s+', chunk.text)
        sub_chunks = []
        current_text = ""
        
        for sentence in sentences:
            if len(current_text + sentence) > self.max_chunk_size and current_text:
                # 현재 텍스트로 청크 생성
                sub_chunk = self._create_sub_chunk(chunk, current_text, len(sub_chunks))
                sub_chunks.append(sub_chunk)
                
                # 오버랩을 위해 마지막 문장들 유지
                overlap_text = self._get_overlap_text(current_text)
                current_text = overlap_text + sentence
            else:
                current_text += sentence + ". "
        
        # 남은 텍스트 처리
        if current_text.strip():
            sub_chunk = self._create_sub_chunk(chunk, current_text, len(sub_chunks))
            sub_chunks.append(sub_chunk)
        
        # 부모-자식 관계 설정
        chunk.child_chunk_ids = [sc.id for sc in sub_chunks]
        for sub_chunk in sub_chunks:
            sub_chunk.parent_chunk_id = chunk.id
        
        return sub_chunks
    
    def _create_sub_chunk(self, parent_chunk: Chunk, text: str, index: int) -> Chunk:
        """서브 청크 생성"""
        self.chunk_counter += 1
        sub_chunk_id = f"{parent_chunk.id}_sub_{index}"
        
        metadata = parent_chunk.metadata.copy()
        metadata.update({
            'parent_chunk_id': parent_chunk.id,
            'sub_chunk_index': index,
            'text_length': len(text),
            'word_count': len(text.split())
        })
        
        return Chunk(
            id=sub_chunk_id,
            text=text.strip(),
            chunk_type=f"{parent_chunk.chunk_type}_sub",
            hierarchy_level=parent_chunk.hierarchy_level + 1,
            metadata=metadata,
            page_nums=parent_chunk.page_nums,
            parent_chunk_id=parent_chunk.id,
            child_chunk_ids=[]
        )
    
    def _get_overlap_text(self, text: str) -> str:
        """오버랩용 텍스트 추출"""
        sentences = text.split('. ')
        if len(sentences) <= 2:
            return ""
        
        overlap_sentences = sentences[-2:]
        return '. '.join(overlap_sentences) + ". "
    
    def _enrich_metadata(self, chunks: List[Chunk], pages_data: List[PageData]) -> List[Chunk]:
        """메타데이터 보강"""
        # 문서 전체 통계
        total_chunks = len(chunks)
        chunk_types = {}
        
        for chunk in chunks:
            chunk_type = chunk.chunk_type
            if chunk_type not in chunk_types:
                chunk_types[chunk_type] = 0
            chunk_types[chunk_type] += 1
            
            # 청크별 추가 메타데이터
            chunk.metadata.update({
                'total_chunks_in_doc': total_chunks,
                'chunk_type_distribution': chunk_types,
                'relative_position': chunks.index(chunk) / total_chunks
            })
        
        return chunks
    
    def get_chunk_summary(self, chunks: List[Chunk]) -> Dict:
        """청킹 결과 요약"""
        summary = {
            'total_chunks': len(chunks),
            'chunk_types': {},
            'hierarchy_levels': {},
            'avg_chunk_size': 0,
            'total_text_length': 0
        }
        
        for chunk in chunks:
            # 타입별 통계
            chunk_type = chunk.chunk_type
            if chunk_type not in summary['chunk_types']:
                summary['chunk_types'][chunk_type] = 0
            summary['chunk_types'][chunk_type] += 1
            
            # 계층별 통계
            level = chunk.hierarchy_level
            if level not in summary['hierarchy_levels']:
                summary['hierarchy_levels'][level] = 0
            summary['hierarchy_levels'][level] += 1
            
            # 텍스트 길이 통계
            summary['total_text_length'] += len(chunk.text)
        
        if chunks:
            summary['avg_chunk_size'] = summary['total_text_length'] / len(chunks)
        
        return summary

def chunk_legal_document(pages_data: List[PageData], max_chunk_size: int = 1000, 
                        overlap_size: int = 100) -> Tuple[List[Chunk], Dict]:
    """법률 문서 청킹 함수 (외부 인터페이스)"""
    chunker = HierarchicalChunker(max_chunk_size, overlap_size)
    chunks = chunker.chunk_pages(pages_data)
    summary = chunker.get_chunk_summary(chunks)
    return chunks, summary