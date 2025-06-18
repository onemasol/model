import pdfplumber
import re
import json
import os
from datetime import datetime


def parse_and_chunk_pdf(pdf_path, max_chunk_len=500):
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            # 조문 번호 기반으로 1차 분리 (예: 1), 2), 3)...)
            primary_split = re.split(r'(?<=\n|\s)(\d+\)\s)', text)
            buffer = ""
            for i in range(0, len(primary_split), 2):
                prefix = primary_split[i].strip()
                content = primary_split[i+1].strip() + primary_split[i+2].strip() if i+2 < len(primary_split) else ""
                full_text = f"{prefix} {content}".strip()
                
                # 길이가 너무 길면 다시 문장 단위로 쪼개기
                if len(full_text) > max_chunk_len:
                    sentences = re.split(r'(?<=[.!?。])\s+', full_text)
                    temp = ""
                    for sentence in sentences:
                        if len(temp) + len(sentence) < max_chunk_len:
                            temp += sentence + " "
                        else:
                            chunks.append({
                                "page": page_num + 1,
                                "content": temp.strip()
                            })
                            temp = sentence + " "
                    if temp:
                        chunks.append({
                            "page": page_num + 1,
                            "content": temp.strip()
                        })
                else:
                    chunks.append({
                        "page": page_num + 1,
                        "content": full_text
                    })
    return chunks


def save_chunks_to_json(chunks, pdf_path, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(pdf_path).replace(".pdf", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f"{filename}_chunks_{timestamp}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✅ JSON 저장 완료: {json_path}")
    return json_path

pdf_path = "C:/rag agent/pdf_data/[별표 14] 업종별시설기준(제36조 관련).pdf"
chunks = parse_and_chunk_pdf(pdf_path)

for i, chunk in enumerate(chunks[:5]):
    print(f"\n[Chunk {i+1} | Page {chunk['page']}]\n{chunk['content']}\n")

# JSON 저장
save_chunks_to_json(chunks, pdf_path)