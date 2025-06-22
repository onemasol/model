"""
PDF 파싱 및 텍스트 추출 모듈
법률 PDF 문서에서 텍스트를 추출하고 구조를 분석하는 기능을 제공
"""

import pdfplumber
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PageData:
    """페이지 데이터 클래스"""
    page_num: int
    text: str
    original_text: str
    structure_type: str
    elements: List[str]

class LegalPDFParser:
    """법률 PDF 파싱 클래스"""
    
    def __init__(self):
        # 법률 문서 패턴 정의
        self.patterns = {
            # 조문 번호 패턴 (1), 2), 3)...)
            'article_number': re.compile(r'(?<=\n|\s)(\d+\)\s)', re.MULTILINE),
            # 항 번호 패턴 (①, ②, ③...)
            'paragraph': re.compile(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]'),
            # 호 번호 패턴 (가., 나., 다...)
            'item': re.compile(r'[가-힣]\.\s'),
            # 조문 제목 패턴 (제n조)
            'law_article': re.compile(r'제\s*(\d+)\s*조\s*(?:\(([^)]+)\))?'),
            # 별표 번호 패턴
            'table': re.compile(r'\[별표\s*(\d+)\]'),
            # 장/절 패턴
            'chapter': re.compile(r'제\s*(\d+)\s*장\s*([^\n\r]+)', re.MULTILINE),
            'section': re.compile(r'제\s*(\d+)\s*절\s*([^\n\r]+)', re.MULTILINE)
        }
    
    def extract_pages_from_pdf(self, pdf_path: str) -> List[PageData]:
        """PDF에서 페이지별 텍스트 추출 및 구조 분석"""
        pages_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"PDF 파일 열기 성공: {pdf_path}")
                logger.info(f"총 페이지 수: {len(pdf.pages)}")
                
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        # 텍스트 정제
                        cleaned_text = self._clean_text(text)
                        
                        # 구조 분석
                        structure_info = self._analyze_page_structure(cleaned_text)
                        
                        page_data = PageData(
                            page_num=page_num + 1,
                            text=cleaned_text,
                            original_text=text,
                            structure_type=structure_info['type'],
                            elements=structure_info['elements']
                        )
                        pages_data.append(page_data)
                        
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생: {e}")
            raise
        
        logger.info(f"텍스트 추출 완료: {len(pages_data)}개 페이지")
        return pages_data
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        # 연속된 공백을 하나로 통합
        text = re.sub(r'\s+', ' ', text)
        # 페이지 번호나 헤더/푸터 제거
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        # 불필요한 특수문자 정리 (법률 문서에 필요한 문자는 유지)
        text = re.sub(r'[^\w\s\(\)①-⑮가-힣.,;:\-\[\]\"\'\/\=\+\%\&\*\#\@\!\?]+', '', text)
        return text.strip()
    
    def _analyze_page_structure(self, text: str) -> Dict:
        """페이지의 법률 구조 분석"""
        structure_info = {
            'type': 'unknown',
            'elements': []
        }
        
        # 법조문 패턴 확인 (제n조)
        law_articles = self.patterns['law_article'].findall(text)
        if law_articles:
            structure_info['type'] = 'law_articles'
            structure_info['elements'] = [f"제{num}조" + (f"({title})" if title else "") 
                                        for num, title in law_articles]
            return structure_info
        
        # 별표 패턴 확인
        tables = self.patterns['table'].findall(text)
        if tables:
            structure_info['type'] = 'table_format'
            structure_info['elements'] = [f"별표 {num}" for num in tables]
            return structure_info
        
        # 조문 번호 패턴 확인 (1), 2), 3)...)
        article_numbers = self.patterns['article_number'].findall(text)
        if article_numbers:
            structure_info['type'] = 'article_numbers'
            structure_info['elements'] = [num.strip() for num in article_numbers]
            return structure_info
        
        # 장/절 패턴 확인
        chapters = self.patterns['chapter'].findall(text)
        sections = self.patterns['section'].findall(text)
        if chapters or sections:
            structure_info['type'] = 'structural'
            structure_info['elements'] = ([f"제{num}장 {title}" for num, title in chapters] + 
                                        [f"제{num}절 {title}" for num, title in sections])
            return structure_info
        
        structure_info['type'] = 'plain_text'
        return structure_info
    
    def get_document_metadata(self, pages_data: List[PageData]) -> Dict:
        """문서 전체 메타데이터 추출"""
        metadata = {
            'total_pages': len(pages_data),
            'structure_types': {},
            'total_elements': 0,
            'document_title': self._extract_document_title(pages_data),
            'main_structure_type': 'unknown'
        }
        
        # 구조 타입별 통계
        for page_data in pages_data:
            structure_type = page_data.structure_type
            if structure_type not in metadata['structure_types']:
                metadata['structure_types'][structure_type] = 0
            metadata['structure_types'][structure_type] += 1
            metadata['total_elements'] += len(page_data.elements)
        
        # 주요 구조 타입 결정
        if metadata['structure_types']:
            metadata['main_structure_type'] = max(
                metadata['structure_types'].items(), 
                key=lambda x: x[1]
            )[0]
        
        return metadata
    
    def _extract_document_title(self, pages_data: List[PageData]) -> str:
        """문서 제목 추출"""
        if not pages_data:
            return "알 수 없는 문서"
        
        first_page_text = pages_data[0].text
        lines = first_page_text.split('\n')[:10]  # 상위 10줄에서 제목 찾기
        
        for line in lines:
            line = line.strip()
            # 법률 문서 제목 패턴
            if ('법' in line or '규칙' in line or '시행령' in line or '별표' in line) and len(line) < 100:
                return line
        
        return "알 수 없는 법률 문서"
    
    def extract_full_text(self, pages_data: List[PageData]) -> str:
        """전체 텍스트를 하나의 문서로 결합"""
        full_text = ""
        for page_data in pages_data:
            full_text += f"\n--- 페이지 {page_data.page_num} ---\n"
            full_text += page_data.text + "\n"
        return full_text.strip()
    
    def find_cross_references(self, pages_data: List[PageData]) -> List[Dict]:
        """문서 내 상호 참조 찾기"""
        references = []
        reference_pattern = re.compile(r'제\s*(\d+)\s*조|제\s*(\d+)\s*항|별표\s*(\d+)')
        
        for page_data in pages_data:
            matches = reference_pattern.finditer(page_data.text)
            for match in matches:
                references.append({
                    'page': page_data.page_num,
                    'reference_text': match.group(),
                    'position': match.start(),
                    'context': page_data.text[max(0, match.start()-50):match.end()+50]
                })
        
        return references

def parse_pdf_file(pdf_path: str) -> tuple[List[PageData], Dict]:
    """PDF 파일 파싱 함수 (외부 인터페이스)"""
    parser = LegalPDFParser()
    pages_data = parser.extract_pages_from_pdf(pdf_path)
    metadata = parser.get_document_metadata(pages_data)
    return pages_data, metadata

if __name__ == "__main__":
    # 테스트 실행
    test_pdf_path = "C:/rag agent/pdf_data/[별표 14] 업종별시설기준(제36조 관련).pdf"
    
    try:
        pages_data, metadata = parse_pdf_file(test_pdf_path)
        
        print(f"\n=== 파싱 결과 ===")
        print(f"문서 제목: {metadata['document_title']}")
        print(f"총 페이지: {metadata['total_pages']}")
        print(f"주요 구조: {metadata['main_structure_type']}")
        print(f"구조 타입별 통계: {metadata['structure_types']}")
        
        # 처음 2페이지 내용 출력
        for i, page_data in enumerate(pages_data[:2]):
            print(f"\n--- 페이지 {page_data.page_num} ---")
            print(f"구조 타입: {page_data.structure_type}")
            print(f"요소들: {page_data.elements[:5]}...")  # 처음 5개만
            print(f"내용: {page_data.text[:200]}...")
            
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")