#!/usr/bin/env python3
"""노션 토글(md export에서는 들여쓴 내용이 딸린 `- 목록 항목`)을 접히는 <details> 블록으로 바꾼다.

어떤 목록 항목이 토글인지는 자동으로 알 수 없다 (평범한 중첩 목록과 모양이 같다). PDF에서 ▼를 확인한 뒤
이 스크립트에 제목을 알려 준다. apply_layout.py보다 **먼저** 실행한다 — 토글 안의 이미지는 들여써져 있어서
풀어 주기 전에는 apply_layout이 찾지 못한다.

사용법:
  convert_toggle.py <슬러그> "<토글 제목의 일부>" ["<다른 토글 제목>" ...]
"""
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_notion import find_repo, inner_breaks  # noqa: E402


def convert(lines, needle):
    hits = [i for i, l in enumerate(lines) if re.match(r"^- ", l) and needle in l]
    if len(hits) != 1:
        sys.exit(f"'{needle}': 줄 맨 앞의 목록 항목으로 정확히 1번 나와야 하는데 {len(hits)}번 나옵니다.")
    start = hits[0]
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith("    ")):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    body = textwrap.dedent("\n".join(lines[start + 1:end])).strip("\n").split("\n")
    if not any(l.strip() for l in body):
        sys.exit(f"'{needle}': 딸린 내용이 없습니다. 토글이 아니라 평범한 목록 항목일 수 있습니다.")
    # 빈 줄이 연달아 있으면 하나로 줄인다 (노션 export가 토글 첫머리에 빈 줄을 두 개 넣는다)
    squeezed = []
    for l in body:
        if l.strip() or (squeezed and squeezed[-1].strip()):
            squeezed.append(l)
    title = lines[start][2:].strip()
    title = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", title)
    block = ['<details markdown="1">', f"<summary>{title}</summary>", ""] + inner_breaks(squeezed) + ["", "</details>"]
    return lines[:start] + block + lines[end:], len(squeezed)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    repo = find_repo(Path(__file__).resolve().parent)
    hits = list((repo / "_posts" / "ai_paper_reviews").glob(f"*-{sys.argv[1]}.md"))
    if len(hits) != 1:
        sys.exit(f"슬러그 '{sys.argv[1]}'에 해당하는 포스트가 {len(hits)}개입니다.")
    lines = hits[0].read_text(encoding="utf-8").split("\n")
    for needle in sys.argv[2:]:
        lines, n = convert(lines, needle)
        print(f"  토글 '{needle}' → <details> ({n}줄)")
    hits[0].write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
