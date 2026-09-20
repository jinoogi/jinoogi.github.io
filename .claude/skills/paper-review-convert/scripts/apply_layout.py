#!/usr/bin/env python3
"""PDF를 보고 정한 이미지 레이아웃을 포스트에 적용한다 (판단은 사람/모델이, 치환은 이 스크립트가).

손으로 HTML을 붙여 넣다 생기는 실수(닫는 태그 누락, 캡션 중복, 엉뚱한 그림 교체)를 막기 위해,
모든 치환은 "그 그림이 정확히 한 번 나오는지" 확인한 뒤에만 수행한다. 하나라도 어긋나면 아무것도 쓰지 않고 멈춘다.

사용법:
  apply_layout.py <슬러그> <spec.json>

spec.json 예시:
  [
    {"fig": 1, "w": 48, "alt": "파라미터 수 대비 정확도"},
    {"row": [{"fig": 2, "w": 50, "alt": "..."}, {"fig": 3, "w": 48, "alt": "..."}]},
    {"fig": 4, "w": 50, "alt": "...", "caption": true},
    {"fig": 5, "alt": "전체 폭 그림은 alt만 바꾼다"}
  ]

- w: 본문 폭 대비 %. 생략하거나 100이고 캡션도 없으면 마크다운 이미지를 그대로 두고 alt만 바꾼다.
- caption: true면 노션이 alt에 넣어 둔 문구를 캡션으로 쓴다. 문자열이면 그 문구를 쓴다 (md가 캡션을 빠뜨려 PDF에서 복원할 때).
  어느 쪽이든 이미지 바로 아래에 같은 문구의 줄이 떠 있으면 중복이므로 지운다.
- row 안의 항목을 {"col": [{"fig": 7, ...}, {"fig": 8, ...}], "w": 44}로 쓰면 그 칸에 그림들을 세로로 쌓는다
  (노션 단 나누기에서 한쪽 단에 그림이 여러 장 들어간 경우).
- row: 나란히 배치. 옵션으로 "align"(기본 flex-start), "justify"(예: space-evenly)를 row와 같은 객체에 둘 수 있다.
"""
import json
import re
import sys
from pathlib import Path

CAPTION_STYLE = "text-align:center; font-size:0.85em; color:gray;"


def find_repo(start):
    for p in [start, *start.parents]:
        if (p / "_config.yml").exists():
            return p
    sys.exit("저장소 루트(_config.yml)를 찾지 못했습니다.")


class Post:
    def __init__(self, path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").split("\n")

    def locate(self, n):
        pat = re.compile(rf"^!\[(?P<alt>[^\]]*)\]\((?P<src>/assets/img/ai_paper_reviews/[^)\s]*-fig{n}\.[A-Za-z]+)\)\s*$")
        hits = [(i, pat.match(l)) for i, l in enumerate(self.lines) if pat.match(l)]
        if len(hits) != 1:
            sys.exit(f"fig{n}: 줄 맨 앞의 마크다운 이미지로 정확히 1번 나와야 하는데 {len(hits)}번 나옵니다. "
                     f"(토글 안에 들여써져 있다면 먼저 <details>로 풀어 주세요)")
        i, m = hits[0]
        return i, m.group("alt"), m.group("src")

    def caption_span(self, i, caption):
        """이미지 아래에 떠 있는 캡션 줄의 인덱스를 돌려준다 (없으면 None)."""
        j = i + 1
        while j < len(self.lines) and not self.lines[j].strip():
            j += 1
        if j < len(self.lines) and self.lines[j].strip() == caption.strip():
            return j
        return None


def figure_html(src, alt, width, caption, indent, centered):
    margin = "0 auto" if centered else "0"
    pad = " " * indent
    out = [f'{pad}<figure style="width:{width}%; margin:{margin};">',
           f'{pad}  <img src="{src}" alt="{alt}" style="width:100%;">']
    if caption:
        out += [f'{pad}  <figcaption style="{CAPTION_STYLE}">', f"{pad}    {caption}", f"{pad}  </figcaption>"]
    out.append(f"{pad}</figure>")
    return out


def resolve(post, item):
    i, old_alt, src = post.locate(item["fig"])
    cap = item.get("caption")
    caption = old_alt if cap is True else (cap or None)
    end = i
    if caption:
        j = post.caption_span(i, caption)
        if j is None and cap is True:
            j = post.caption_span(i, old_alt)
        if j is not None:
            end = j
    # figcaption은 날 HTML이라 안쪽의 마크다운이 처리되지 않는다. 노션이 캡션에 넣어 둔 **굵게**는 태그로 바꾼다.
    caption_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", caption) if caption else None
    alt = item.get("alt", old_alt.replace("*", "")).replace('"', "&quot;")
    return {"start": i, "end": end, "src": src, "alt": alt, "w": item.get("w", 100), "caption": caption_html}


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    repo = find_repo(Path(__file__).resolve().parent)
    hits = list((repo / "_posts" / "ai_paper_reviews").glob(f"*-{sys.argv[1]}.md"))
    if len(hits) != 1:
        sys.exit(f"슬러그 '{sys.argv[1]}'에 해당하는 포스트가 {len(hits)}개입니다.")
    post = Post(hits[0])
    spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

    edits = []  # (start, end, new_lines, 설명)
    for op in spec:
        if "row" in op:
            cells = [{"w": it["w"], "figs": [resolve(post, f) for f in it["col"]]} if "col" in it
                     else {"w": None, "figs": [resolve(post, it)]} for it in op["row"]]
            figs = [f for c in cells for f in c["figs"]]
            for a, b in zip(figs, figs[1:]):
                between = post.lines[a["end"] + 1:b["start"]]
                if any(l.strip() for l in between):
                    sys.exit(f"row: fig 사이에 다른 내용이 끼어 있어 나란히 묶을 수 없습니다: {between}")
            total = sum(c["w"] if c["w"] is not None else c["figs"][0]["w"] for c in cells)
            if total > 99:
                sys.exit(f"row: 폭 합계가 {total}%입니다. gap 때문에 99% 이하여야 한 줄에 들어갑니다.")
            style = f"display:flex; gap:12px; align-items:{op.get('align', 'flex-start')};"
            if op.get("justify"):
                style += f" justify-content:{op['justify']};"
            block = [f'<div style="{style}">']
            for c in cells:
                if c["w"] is None:
                    f = c["figs"][0]
                    block += figure_html(f["src"], f["alt"], f["w"], f["caption"], 2, centered=False)
                else:  # 한 칸 안에 그림을 세로로 쌓는다
                    block.append(f'  <div style="width:{c["w"]}%; display:flex; flex-direction:column; gap:12px;">')
                    for f in c["figs"]:
                        block += figure_html(f["src"], f["alt"], 100, f["caption"], 4, centered=False)
                    block.append("  </div>")
            block.append("</div>")
            widths = [f"{c['w']}%(세로 {len(c['figs'])}장)" if c["w"] is not None else f"{c['figs'][0]['w']}%" for c in cells]
            edits.append((figs[0]["start"], figs[-1]["end"], block, "나란히 " + " : ".join(widths)))
        else:
            f = resolve(post, op)
            if f["w"] >= 100 and not f["caption"]:
                edits.append((f["start"], f["end"], [f"![{op.get('alt', '')}]({f['src']})"] if op.get("alt")
                              else [post.lines[f["start"]]], "전체 폭 (alt만)"))
            else:
                edits.append((f["start"], f["end"],
                              figure_html(f["src"], f["alt"], min(f["w"], 100), f["caption"], 0, centered=True),
                              f"단독 {min(f['w'], 100)}%" + (" + 캡션" if f["caption"] else "")))

    spans = sorted((s, e) for s, e, _, _ in edits)
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        if s2 <= e1:
            sys.exit("같은 그림이 두 번 지정됐거나 구간이 겹칩니다.")
    for s, e, new, desc in sorted(edits, key=lambda x: -x[0]):
        post.lines[s:e + 1] = new
    post.path.write_text("\n".join(post.lines), encoding="utf-8")
    for s, e, new, desc in sorted(edits, key=lambda x: x[0]):
        print(f"  {desc}")
    print(f"{post.path.name}: {len(edits)}건 적용")


if __name__ == "__main__":
    main()
