import requests
from bs4 import BeautifulSoup
import json

url = "https://health.gangnam.go.kr/web/hygiene/hygiene/standards/sub01.do"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, "html.parser")

result = []

for h3 in soup.select("h3.h3_tit"):
    title = h3.get_text(strip=True)
    current = h3
    subitems = []

    while True:
        current = current.find_next_sibling()
        if current is None:
            break
        if current.name == "h3" and "h3_tit" in current.get("class", []):
            break

        if current.name == "h4":
            subtitle = current.get_text(strip=True)
            table_wrapper = current.find_next_sibling("div", class_="conTableGroup")
            if not table_wrapper:
                continue

            table = table_wrapper.find("table", class_="conTable")
            if not table:
                continue

            data = []
            for tr in table.select("tbody tr"):
                th = tr.find("th", scope="row")
                td = tr.find("td")
                if th and td:
                    data.append({
                        "구분": th.get_text(strip=True),
                        "내용": td.get_text(" ", strip=True)
                    })

            subitems.append({
                "소제목": subtitle,
                "데이터": data
            })

    result.append({
        "제목": title,
        "항목들": subitems
    })

with open("gangnam_hygiene_data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ JSON 파일 저장 완료: gangnam_hygiene_data.json")
