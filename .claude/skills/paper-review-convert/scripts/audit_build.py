#!/usr/bin/env python3
"""빌드된 논문리뷰 페이지에서 "마크다운/수식이 변환되지 않고 날것으로 나간 흔적"을 찾는다.

tools/test.sh(htmlproofer)는 링크 무결성만 검사한다. HTML 블록이 제대로 닫히지 않아 문서 뒷부분이
통째로 마크다운 처리 없이 출력되는 사고는 링크가 멀쩡하므로 그대로 통과한다 (BatchNorm 글에서 실제 발생).
이 스크립트는 _site의 결과물을 직접 읽어 그런 흔적을 잡는다. 반드시 빌드(tools/test.sh) 후에 실행한다.

사용법:
  audit_build.py            _posts/ai_paper_reviews 의 모든 글 검사
  audit_build.py u-net vit  지정한 슬러그만 검사
종료 코드: 문제가 있으면 1
"""
import re
import sys
from pathlib import Path


def find_repo(start):
    for p in [start, *start.parents]:
        if (p / "_config.yml").exists():
            return p
    sys.exit("저장소 루트(_config.yml)를 찾지 못했습니다.")


# (설명, 정규식, 검사 대상) — 대상이 "html"이면 태그 포함 원문, "text"면 태그·코드블록을 걷어낸 본문 텍스트
CHECKS = [
    ("글자로 삼켜진 HTML 태그 (블록이 안 닫혔을 가능성 — 닫는 태그 들여쓰기 확인)",
     r"&lt;/?(?:div|details|summary|figure|figcaption|aside|iframe)\b", "html"),
    ("변환 안 된 $$ 수식", r"\$\$", "text"),
    ("변환 안 된 한 겹 $ 수식", r"(?<![\$\\])\$(?!\$)[^$\n]{1,80}?\\[a-zA-Z]+[^$\n]{0,80}?\$(?!\$)", "text"),
    ("날것의 마크다운 제목 (## ...)", r"(?m)^\s*#{1,6} \S", "text"),
    ("날것의 마크다운 이미지 (![...](...))", r"!\[[^\]]*\]\(", "text"),
    ("날것의 굵은 글씨 (**...**)", r"\*\*\S", "text"),
    ("수식 밖에 남은 LaTeX 환경 (\\begin{...})", r"\\begin\{", "text_nomath"),
    ("중복 줄바꿈 <br><br> (hard_wrap이 적용되는 일반 본문에 <br>을 넣었을 가능성)",
     r"<br\s*/?>\s*<br\s*/?>", "html"),
    ("노션 내부 주소 잔재", r"notion://|notion\.so/", "html"),
    ("변환 안 된 <aside>", r"&lt;aside|<aside", "html"),
]


def article_of(html):
    m = re.search(r'<div class="content">(.*?)<div class="post-tail-wrapper', html, re.S)
    return m.group(1) if m else html


def to_text(fragment, drop_math=False):
    fragment = re.sub(r"<pre\b.*?</pre>|<code\b.*?</code>", " ", fragment, flags=re.S)
    if drop_math:
        fragment = re.sub(r"\\\[.*?\\\]|\\\(.*?\\\)", " ", fragment, flags=re.S)
    return re.sub(r"<[^>]+>", " ", fragment)


def main():
    repo = find_repo(Path(__file__).resolve().parent)
    site = repo / "_site" / "posts"
    if not site.exists():
        sys.exit("_site/posts 가 없습니다. 먼저 tools/test.sh 로 빌드하세요.")
    slugs = sys.argv[1:] or sorted(
        re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem) for p in (repo / "_posts" / "ai_paper_reviews").glob("*.md"))

    failed = 0
    for slug in slugs:
        page = site / slug / "index.html"
        if not page.exists():
            print(f"FAIL  {slug}: 빌드 결과가 없음 (미래 날짜이거나 파일명 형식 오류로 누락됐을 수 있음)")
            failed += 1
            continue
        art = article_of(page.read_text(encoding="utf-8"))
        views = {"html": art, "text": to_text(art), "text_nomath": to_text(art, drop_math=True)}
        problems = []
        for desc, pattern, target in CHECKS:
            hits = re.findall(pattern, views[target])
            if hits:
                m = re.search(pattern, views[target])
                ctx = re.sub(r"\s+", " ", views[target][max(0, m.start() - 30):m.end() + 50]).strip()
                problems.append(f"{desc}: {len(hits)}건  예) …{ctx}…")
        # kramdown은 `|`가 든 줄이 문단 첫 줄이면 표로 해석한다 (링크 제목의 "A | B", 수식 밖의 p(x|z) 등).
        # 원본 md에 있는 표의 수와 결과물의 표 수가 다르면 그런 오인이 일어난 것이다. 코드블록(rouge)의 표는 제외.
        src = next((repo / "_posts" / "ai_paper_reviews").glob(f"*-{slug}.md"), None)
        if src:
            md_tables = len(re.findall(r"(?m)^\|.*\|[ \t]*\n\|[ \t:|-]+\|[ \t]*$", src.read_text(encoding="utf-8")))
            html_tables = len(re.findall(r"<table(?![^>]*rouge)", art))
            if html_tables != md_tables:
                problems.append(f"표 개수 불일치: 원본 md {md_tables}개, 결과물 {html_tables}개 "
                                f"(`|`가 든 줄이 표로 오인됐을 수 있음 — `\\|`로 이스케이프)")
        n_math = len(re.findall(r"\\[\(\[]", art))
        if problems:
            failed += 1
            print(f"FAIL  {slug}")
            for p in problems:
                print(f"        - {p}")
        else:
            print(f"OK    {slug}  (제목 {len(re.findall(r'<h[2-4]', art))}개, 수식 {n_math}개, 이미지 {art.count('<img')}개)")
    print(f"\n{len(slugs) - failed}/{len(slugs)} 통과")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
