#!/usr/bin/env python3
"""노션 일반 문서 export → Jekyll 포스트 변환 (판단이 필요 없는 기계적 변환 전담). 논문리뷰는 다루지 않는다.

한 번에 한 문서씩 변환한다. 카테고리와 슬러그는 호출할 때 지정한다 (목록 파일·진행상황 파일 없음).
쓰기 범위: _posts/<대분류 폴더>/, assets/img/<대분류 폴더>/ — 대분류 폴더는 CATEGORIES 참고.
논문리뷰 폴더(_posts/ai_paper_reviews)에는 쓰지 않는다. 원본(blog_source/노션문서 마이그레이션)은 읽기만 한다.
git 명령은 실행하지 않는다.

사용법:
  convert_doc.py --list                         원본 폴더의 문서와 PDF 유무 출력
  convert_doc.py "유체역학 1장" --slug fluid-mechanics-ch1 --category "기계공학, 유체역학" --dry-run
  convert_doc.py "유체역학 1장" --slug fluid-mechanics-ch1 --category "기계공학, 유체역학"

  --title "..."   노션 제목 대신 쓸 제목
  --new-category  CATEGORIES에 없는 소분류를 새로 만든다 (사용자가 새 카테고리라고 확인한 경우에만)
  --force         같은 슬러그의 기존 포스트를 덮어쓴다 (날짜는 기존 글의 것을 유지)
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import textwrap
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote

# 블로그 카테고리 구조 (2026-09-20 확정). 대분류 → (포스트·이미지 폴더 이름, 소분류 목록)
CATEGORIES = {
    "AI Study Notes": ("ai_study_notes", ["Linear Algebra", "Probability & Statistics", "Optimization",
                                          "Machine Learning", "Reinforcement Learning", "PyTorch"]),
    "CS": ("cs", ["웹개발", "알고리즘", "컴퓨터시스템", "pintOS"]),
    "기계공학": ("mechanical_engineering", ["유체역학", "열전달", "동역학", "제어공학"]),
    "반도체": ("semiconductor", ["물리전자", "기초반도체공학", "반도체공정"]),
    "프로젝트": ("projects", []),
}

AVATAR_EMOJI_ID = "2a3b9c4a"  # 사용자의 아바타 커스텀 이모지 (논문리뷰 70편 중 42회 사용)
MAX_WIDTH = 1600
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
KST = timezone(timedelta(hours=9))

# 닫는 태그를 들여쓰지 않는 이유: 내용이 목록으로 끝날 때 들여쓴 </div>는 목록 항목의 이어지는 내용으로
# 해석되어 블록이 닫히지 않고, 그 뒤 문서 전체의 마크다운 처리가 꺼진다 (BatchNorm 글에서 실제로 발생).
CALLOUT = """<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>{icon}</div>
<div markdown="1" style="flex:1; min-width:0;">

{content}

</div>
</div>"""


def norm(s):
    # 한글 제목을 비교해야 하므로 한글도 남긴다. macOS 파일명은 자모가 분리된 NFD로 올 수 있어 NFC로 맞춘다.
    return re.sub(r"[^0-9a-z가-힣]", "", unicodedata.normalize("NFC", s).lower())


def find_repo(start):
    for p in [start, *start.parents]:
        if (p / "_config.yml").exists():
            return p
    sys.exit("저장소 루트(_config.yml)를 찾지 못했습니다.")


def is_post_of(path, slug):
    return re.fullmatch(rf"\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(slug)}", path.stem) is not None


def posts_with_slug(repo, slug):
    """글 주소(/posts/<슬러그>/)는 폴더와 상관없이 모든 글이 공유하므로, 충돌 확인은 _posts 전체에서 한다."""
    return [p for p in (repo / "_posts").rglob("*.md") if is_post_of(p, slug)]


def own_posts(repo):
    """이 스킬이 관리하는 폴더의 글 전부 (논문리뷰 폴더는 제외)."""
    return sorted(p for d, _ in CATEGORIES.values() for p in (repo / "_posts" / d).glob("*.md"))


def find_post(repo, slug):
    hits = [p for p in own_posts(repo) if is_post_of(p, slug)]
    if len(hits) != 1:
        sys.exit(f"슬러그 '{slug}'에 해당하는 포스트가 {len(hits)}개입니다 (논문리뷰 글은 이 스킬의 대상이 아닙니다).")
    return hits[0]


def hint(name, choices):
    # 글자 하나만 달라도 새 카테고리가 생긴다. 대소문자·띄어쓰기만 다른 기존 이름이 있으면 알려 준다.
    close = [c for c in choices if norm(c) == norm(name)]
    return f" (혹시 '{close[0]}'?)" if close else ""


def parse_category(text, allow_new):
    parts = [p.strip() for p in re.split(r"[,>]", text) if p.strip()]
    if not 1 <= len(parts) <= 2:
        sys.exit(f"카테고리는 '대분류, 소분류' 또는 '대분류' 형식이어야 합니다: {text}")
    top, sub = parts[0], (parts[1] if len(parts) == 2 else None)
    if top == "AI Paper Reviews":
        sys.exit("AI Paper Reviews는 이 스킬이 아니라 paper-review-convert로 옮깁니다.")
    if top not in CATEGORIES:
        sys.exit(f"대분류 '{top}'가 없습니다{hint(top, CATEGORIES)}. 가능한 대분류: {', '.join(CATEGORIES)}")
    subs = CATEGORIES[top][1]
    if sub and sub not in subs and not allow_new:
        sys.exit(f"'{top}'에 소분류 '{sub}'가 없습니다{hint(sub, subs)}. 기존 소분류: {', '.join(subs) or '없음'}\n"
                 "오타가 아니라 새 카테고리를 만드는 것이면 --new-category를 붙이세요.")
    return top, sub


class Converter:
    def __init__(self, repo):
        self.repo = repo
        self.src = repo / "blog_source" / "노션문서 마이그레이션"
        if not self.src.exists():
            sys.exit(f"원본 폴더가 없습니다: {self.src.relative_to(repo)} (노션 export의 md·이미지 폴더·PDF를 넣어 주세요)")
        self.mds = self._index_mds()
        self.pdf_of = self._index_pdfs()

    def _index_mds(self):
        out = []
        for f in sorted(self.src.glob("*.md")):
            out.append((re.sub(r"\s+[0-9a-f]{32}$", "", unicodedata.normalize("NFC", f.stem)), f))
        return out

    def _index_pdfs(self):
        out = {}
        for f in [*self.src.glob("*.pdf"), *self.src.glob("pdf/*.pdf")]:
            # 노션 export 방식에 따라 파일명이 세 가지로 나온다:
            #   <uuid>%2F<이름>.pdf  /  <uuid>_<이름>.pdf  /  <이름> <32자리 해시>.pdf
            # 첫 번째 형식은 이름도 %인코딩되어 한글 제목이 `%EC%9B%A8...`로 온다 (웨이퍼냉각시스템에서 발견)
            name = unicodedata.normalize("NFC", unquote(f.stem)).split("/")[-1]
            name = re.sub(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}_", "", name)
            name = re.sub(r"\s+[0-9a-f]{32}$", "", name)
            out[norm(name)] = f
        return out

    def print_list(self):
        if not self.mds:
            print("원본 폴더에 md가 없습니다.")
            return
        for name, _ in self.mds:
            print(f"{'O' if norm(name) in self.pdf_of else '-'}  {name}")
        print("\n(O = PDF 있음)")

    def find_md(self, query):
        key = norm(query)
        exact = [m for m in self.mds if norm(m[0]) == key]
        hits = exact or [m for m in self.mds if key and key in norm(m[0])]
        if len(hits) != 1:
            names = ", ".join(n for n, _ in hits) or "없음"
            sys.exit(f"'{query}'에 해당하는 md가 {len(hits)}개입니다 ({names}). --list로 이름을 확인하세요.")
        return hits[0]

    def convert(self, query, slug, category, title=None, dry_run=False, force=False, new_category=False):
        name, md_path = self.find_md(query)
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            sys.exit(f"슬러그는 영문 소문자·숫자·하이픈만 씁니다 (글 주소가 됩니다): {slug}")
        top, sub = parse_category(category, new_category)
        pdir = CATEGORIES[top][0]
        existing = posts_with_slug(self.repo, slug)
        if existing and not force:
            print(f"[건너뜀] 같은 슬러그의 글이 이미 있습니다: {existing[0].relative_to(self.repo)}")
            return
        if existing and existing[0].parent != self.repo / "_posts" / pdir:
            sys.exit(f"--force로도 덮어쓰지 않습니다: {existing[0].relative_to(self.repo)}는 다른 폴더의 글입니다. "
                     "주소가 겹치는 것이면 슬러그를 바꾸고, 카테고리를 옮기는 것이면 기존 글을 지운 뒤 다시 변환하세요.")
        if existing:
            post_path = existing[0]
            m = re.search(r"^date: (.+)$", post_path.read_text(encoding="utf-8"), flags=re.M)
            date_str = m.group(1) if m else f"{post_path.stem[:10]} 00:00:00 +0900"
        else:
            # 미래 날짜의 글은 Jekyll이 빌드에서 조용히 제외한다. 빌드는 변환 뒤에 하므로 1분 전 시각이면 안전하다.
            now = datetime.now(KST).replace(second=0, microsecond=0) - timedelta(minutes=1)
            post_path = self.repo / "_posts" / pdir / f"{now:%Y-%m-%d}-{slug}.md"
            date_str = f"{now:%Y-%m-%d %H:%M:%S} +0900"
        report = {"images": [], "missing": [], "callouts": 0, "custom_emoji": []}

        body = md_path.read_text(encoding="utf-8")
        h1 = re.match(r"\A\s*# (.*)\n+", body)
        if h1:
            body = body[h1.end():]
        title = title or (h1.group(1).strip() if h1 else name)
        body = self._migrate_images(body, title, slug, pdir, dry_run, report)
        body = self._convert_callouts(body, report)  # 콜아웃 안의 커스텀 이모지는 여기서 대체 아이콘으로 바뀐다
        # 콜아웃 밖에 남은 커스텀 이모지: notion:// 내부 주소라 밖에서는 깨진 이미지가 되므로 걷어낸다
        body, stray = re.subn(r'^[ \t]*<img src="notion://[^>]*>[ \t]*\n', "", body, flags=re.M)
        report["custom_emoji"] += ["콜아웃 밖 → 제거"] * stray
        body = protect_inline_math(body)

        cats = ", ".join(c for c in (top, sub) if c)
        # 한글 제목에 `:` 등이 들어가도 YAML이 깨지지 않도록 따옴표로 감싼다 (JSON 문자열은 유효한 YAML이다)
        front = (f"---\ntitle: {json.dumps(title, ensure_ascii=False)}\ndate: {date_str}\n"
                 f"categories: [{cats}]\nmath: true\n---\n\n")

        key = norm(name)
        tag = "[dry-run] " if dry_run else ""
        print(f"{tag}{title}")
        print(f"  원본     : {md_path.name}")
        print(f"  포스트   : {post_path.relative_to(self.repo)}{'  (덮어씀)' if existing else ''}")
        print(f"  주소     : /posts/{slug}/")
        print(f"  카테고리 : {' > '.join(c for c in (top, sub) if c)}"
              f"{'  (새 소분류)' if sub and sub not in CATEGORIES[top][1] else ''}")
        print(f"  날짜     : {date_str}")
        print(f"  PDF      : {'있음 → ' + self.pdf_of[key].name if key in self.pdf_of else '없음 (레이아웃 설계 불가)'}")
        print(f"  이미지   : {len(report['images'])}개")
        for src, dest, resized in report["images"]:
            print(f"    {src}  →  {dest}{'  (축소)' if resized else ''}")
        for m in report["missing"]:
            print(f"    [경고] 파일 없음: {m}")
        print(f"  콜아웃   : {report['callouts']}개 변환")
        for note in report["custom_emoji"]:
            print(f"  커스텀 이모지 : {note}")
        if re.search(r"^- .+\n {4}\S|^- .+\n\s*\n {4}\S", body, flags=re.M):
            print("  토글 의심 : 들여쓴 내용이 딸린 목록 항목 있음 (PDF에서 ▼ 토글인지 확인)")
        print(f"  수식     : {'있음' if '$' in body else '없음'}")
        yt = len(re.findall(r"youtu\.?be", body))
        if yt:
            print(f"  유튜브   : 링크 {yt}개 (iframe 임베드 검토)")
        if dry_run:
            return
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(front + body.rstrip() + "\n", encoding="utf-8")

    def _migrate_images(self, body, title, slug, pdir, dry_run, report):
        counter = 0

        def repl(m):
            nonlocal counter
            alt, target = m.group(1), unquote(m.group(2))
            if re.match(r"https?://", target):
                return m.group(0)
            src = self.src / target
            if not src.exists() or src.suffix.lower() not in IMAGE_EXTS:
                report["missing"].append(target)
                return m.group(0)
            counter += 1
            fname = f"{slug}-fig{counter}{src.suffix.lower()}"
            dest = self.repo / "assets" / "img" / pdir / slug / fname
            resized = False
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                resized = self._shrink(dest)
            else:
                resized = self._width(src) > MAX_WIDTH
            report["images"].append((target, f"{pdir}/{slug}/{fname}", resized))
            if Path(alt).suffix.lower() in IMAGE_EXTS or not alt.strip():
                alt = f"{title} figure {counter}"
            return f"![{alt}](/assets/img/{pdir}/{slug}/{fname})"

        return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", repl, body)

    @staticmethod
    def _width(path):
        if path.suffix.lower() in {".gif", ".svg"}:
            return 0
        out = subprocess.run(["sips", "-g", "pixelWidth", str(path)], capture_output=True, text=True).stdout
        m = re.search(r"pixelWidth:\s*(\d+)", out)
        return int(m.group(1)) if m else 0

    def _shrink(self, path):
        if self._width(path) <= MAX_WIDTH:
            return False
        subprocess.run(["sips", "--resampleWidth", str(MAX_WIDTH), str(path)], capture_output=True)
        return True

    def _convert_callouts(self, body, report):
        def repl(m):
            # 토글 안의 콜아웃은 4칸 들여쓰기된 채로 나온다. 그대로 두면 코드블록으로 렌더링된다.
            lines = textwrap.dedent(m.group(1)).strip("\n").splitlines()
            custom = None
            for l in list(lines):
                mm = re.match(r'\s*<img src="notion://custom_emoji/[0-9a-f-]+/([0-9a-f-]+)', l)
                if mm:
                    custom = mm.group(1)
                    lines.remove(l)
            while lines and not lines[0].strip():
                lines.pop(0)
            icon = "💡"
            if lines and len(lines[0].strip()) <= 3 and not any(c.isalnum() for c in lines[0]):
                icon = lines.pop(0).strip()
            while lines and not lines[0].strip():
                lines.pop(0)
            if custom:
                # 노션 커스텀 이모지는 내보낼 수 없어 대체 아이콘을 쓴다 (2026-09-20 사용자 결정).
                # 아바타 이모지는 주로 "느낀점"과 제목 없는 소감에 쓰였다 → 😲.
                # 같은 아바타라도 Motivation·핵심요약 같은 다른 굵은 제목이 붙은 콜아웃에는 😲가 어색하므로 기본값을 쓴다.
                first = lines[0].strip() if lines else ""
                other_title = first.startswith("**") and "느낀점" not in first
                icon = "😲" if custom.startswith(AVATAR_EMOJI_ID) and not other_title else "💡"
                report["custom_emoji"].append(f"'{first[:20]}' 콜아웃 → {icon}")
            report["callouts"] += 1
            return CALLOUT.format(icon=icon, content="\n".join(inner_breaks(tighten(lines))).strip("\n"))

        return re.sub(r"<aside>\s*\n(.*?)\n\s*</aside>", repl, body, flags=re.DOTALL)


def protect_inline_math(body):
    """인라인 수식 $...$를 kramdown이 보호하는 $$...$$ 형태로 바꾼다.

    한 겹 $는 kramdown이 수식으로 인식하지 못해 내부를 마크다운으로 처리하고,
    그 과정에서 \\{ → {, \\\\ → \\ 로 망가진다. $$...$$는 문장 중간에 있으면 인라인 수식으로 보호된다.
    """
    inline = re.compile(r"(?<![\$\\])\$(?!\$)(\S(?:[^$\n]*?\S)?)\$(?!\$)")
    out, fence, display = [], False, False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
        elif not fence and s.startswith("$$") and not (len(s) > 2 and s.endswith("$$")):
            display = not display
            out.append(line)
            continue
        if not fence and not display:
            parts = re.split(r"(`[^`\n]*`)", line)
            line = "".join(p if p.startswith("`") else inline.sub(r"$$\1$$", p) for p in parts)
        out.append(line)
    return "\n".join(out) + ("\n" if body.endswith("\n") else "")


# 목록 기호는 뒤에 공백이 있을 때만 목록이다. `**굵게`로 시작하는 줄을 `* 항목`으로 오인하면 안 된다.
_SPECIAL = re.compile(r"\s*([-*+]\s|[>#|<!]|\d+\.\s|```)")


def _display_line(s):
    # 수식 블록의 울타리(`$$` 단독 줄)이거나 한 줄짜리 디스플레이 수식(`$$...$$`만 있는 줄).
    # `$$x$$가 입력`처럼 인라인 수식으로 시작하는 문장은 일반 텍스트다 — 이걸 울타리로 오인하면
    # 그 뒤 줄들이 전부 "수식 블록 안"으로 취급되어 <br>이 빠진다 (VAE 토글에서 실제 발생).
    return s == "$$" or (len(s) > 4 and s.startswith("$$") and s.endswith("$$") and s.count("$$") == 2)


def _plain(line):
    return bool(line.strip()) and not _SPECIAL.match(line) and not _display_line(line.strip())


def _walk(lines):
    """각 줄이 코드 울타리나 수식 블록의 안쪽인지 함께 돌려준다."""
    fence = display = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
        elif s == "$$":
            display = not display
        yield i, line, fence or display


def tighten(lines):
    """콜아웃 안쪽 전용: 일반 텍스트 줄 사이에 낀 빈 줄을 없앤다.

    노션은 콜아웃 안의 각 줄을 별개 블록으로 내보내므로 md에는 줄마다 빈 줄이 끼지만,
    노션 화면(과 PDF)에서는 제목과 본문이 빈틈없이 붙어 보인다. 목록·수식·코드 주변의 빈 줄은 문법상 필요하므로 남긴다.
    """
    out = []
    for i, line, inside in _walk(lines):
        nxt = next((l for l in lines[i + 1:] if l.strip()), "")
        if not line.strip() and not inside and out and _plain(out[-1]) and _plain(nxt):
            continue
        out.append(line)
    return out


def inner_breaks(lines):
    """markdown="1" HTML 블록 안쪽 전용: 연속된 일반 텍스트 줄 사이에 <br>을 넣는다.

    _config.yml의 hard_wrap은 일반 본문에만 적용되고 HTML 블록 안쪽에는 닿지 않는다.
    그래서 콜아웃 안에서는 <br> 없이는 줄들이 한 줄로 붙는다. (반대로 일반 본문에 <br>을 넣으면 줄바꿈이 두 번 들어간다.)
    """
    out = []
    for i, line, inside in _walk(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if not inside and _plain(line) and _plain(nxt) and not line.rstrip().endswith("<br>"):
            line = line.rstrip() + "<br>"
        out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser(description="노션 일반 문서 export → Jekyll 포스트 변환 (한 문서씩, 논문리뷰 제외)")
    ap.add_argument("name", nargs="?", help="변환할 노션 문서 이름 (일부만 적어도 된다)")
    ap.add_argument("--slug", help="영문 파일명 = 글 주소 /posts/<slug>/")
    ap.add_argument("--category", help='"대분류, 소분류" — 사용자가 정한 그대로')
    ap.add_argument("--title", help="노션 제목 대신 쓸 제목")
    ap.add_argument("--list", action="store_true", help="원본 폴더의 문서와 PDF 유무")
    ap.add_argument("--dry-run", action="store_true", help="쓰지 않고 계획만 출력")
    ap.add_argument("--force", action="store_true", help="같은 슬러그의 기존 포스트를 덮어씀")
    ap.add_argument("--new-category", action="store_true", help="CATEGORIES에 없는 소분류를 새로 만듦")
    args = ap.parse_args()

    conv = Converter(find_repo(Path(__file__).resolve().parent))
    if args.list:
        conv.print_list()
    elif args.name:
        if not args.slug or not args.category:
            ap.error("--slug와 --category가 필요합니다.")
        conv.convert(args.name, args.slug, args.category, title=args.title, dry_run=args.dry_run,
                     force=args.force, new_category=args.new_category)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
