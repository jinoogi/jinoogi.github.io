#!/usr/bin/env python3
"""노션 논문리뷰 export → Jekyll 포스트 변환 (판단이 필요 없는 기계적 변환 전담).

쓰기 범위: _posts/ai_paper_reviews/, assets/img/ai_paper_reviews/, blog_source/migration_status.json
원본(blog_source/논문리뷰 마이그레이션)은 읽기만 한다. git 명령은 실행하지 않는다.

사용법:
  convert_notion.py --list                 전체 논문의 상태표 출력
  convert_notion.py --next 5               다음에 변환할 논문 5편의 이름 출력
  convert_notion.py "U-Net" --dry-run      실제로 쓰지 않고 계획만 출력
  convert_notion.py "U-Net"                변환 실행
  convert_notion.py --mark-layout-done "U-Net"   레이아웃 검수 완료 표시
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

CATEGORIES = {
    "CV & Multimodal": ["VGG", "ResNet", "Batchnorm / Layernorm", "R-CNN", "U-Net", "Mask R-CNN",
                        "ViT", "SimCLR", "VAE", "Diffusion", "CLIP", "LLaVA"],
    "NLP & LLM": ["BPE", "GloVe", "GPT-1", "BERT", "GPT-2", "GPT-3", "FLAN", "Codex", "LLM.int8",
                  "MoE", "Speculative Decoding", "LoRA", "Scaling law"],
    "Reasoning & RL": ["CoT", "PPO", "RLHF", "DPO", "DeepSeek R1", "GRPO", "Inference-time Scaling",
                       "STaR", "AdaSTaR", "PRM"],
    "Agents": ["ReAct", "Toolformer", "Gorilla", "WebGPT", "ADAS", "Web Agent with World Models",
               "Tree search agent", "WEB-SHEPHERD", "SELF-REFINE", "Reflexion", "Search-R1",
               "SkillRL", "FocusAgent", "LCoW"],
    "Memory & Personalization": ["Mem^p", "BESPOKE", "CURIO", "RLPA", "PAHF", "Memskill", "Mem0",
                                 "LoCoMo", "MemCoRL", "LongMemEval", "CER"],
    "RAG": ["RAG", "DPR", "Self-RAG", "GENREAD"],
    "Embodied AI": ["EmbodiedBench", "PIN", "VLingNav"],
    "기타": ["MATE", "Weak driven learning"],
}

AVATAR_EMOJI_ID = "2a3b9c4a"  # 사용자의 아바타 커스텀 이모지 (70편 중 42회 사용)
MAX_WIDTH = 1600
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

# 닫는 태그를 들여쓰지 않는 이유: 내용이 목록으로 끝날 때 들여쓴 </div>는 목록 항목의 이어지는 내용으로
# 해석되어 블록이 닫히지 않고, 그 뒤 문서 전체의 마크다운 처리가 꺼진다 (BatchNorm 글에서 실제로 발생).
CALLOUT = """<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>{icon}</div>
<div markdown="1" style="flex:1; min-width:0;">

{content}

</div>
</div>"""


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def safe_dir(name):
    return re.sub(r"[^A-Za-z0-9.]+", "-", name).strip("-")


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def find_repo(start):
    for p in [start, *start.parents]:
        if (p / "_config.yml").exists():
            return p
    sys.exit("저장소 루트(_config.yml)를 찾지 못했습니다.")


class Migration:
    def __init__(self, repo):
        self.repo = repo
        self.src = repo / "blog_source" / "논문리뷰 마이그레이션"
        self.list_file = repo / "blog_source" / "논문리스트.txt"
        self.status_file = repo / "blog_source" / "migration_status.json"
        self.posts = repo / "_posts" / "ai_paper_reviews"
        self.assets = repo / "assets" / "img" / "ai_paper_reviews"
        self.sub_of = {norm(n): sub for sub, names in CATEGORIES.items() for n in names}
        self.order = self._load_order()
        self.md_of = self._index_mds()
        self.pdf_of = self._index_pdfs()
        self.status = json.loads(self.status_file.read_text()) if self.status_file.exists() else {}

    def _load_order(self):
        order = []
        for line in self.list_file.read_text().splitlines():
            name = re.sub(r"\s*\(\d+\)\s*$", "", line).strip()
            if name and norm(name) not in [norm(n) for n in order]:
                order.append(name)
        return order

    def _index_mds(self):
        out = {}
        for f in self.src.glob("*.md"):
            name = re.sub(r"\s+[0-9a-f]{32}$", "", f.stem)
            out[norm(name)] = (name, f)
        return out

    def _index_pdfs(self):
        out = {}
        pdf_dir = self.src / "pdf"
        if pdf_dir.exists():
            for f in pdf_dir.glob("*.pdf"):
                # 노션 export 방식에 따라 파일명이 세 가지로 나온다:
                #   <uuid>%2F<이름>.pdf  /  <uuid>_<이름>.pdf  /  <이름> <32자리 해시>.pdf
                name = f.stem.split("%2F")[-1]
                name = re.sub(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}_", "", name)
                name = re.sub(r"\s+[0-9a-f]{32}$", "", name)
                out[norm(name)] = f
        return out

    def existing_post(self, slug):
        hits = list(self.posts.glob(f"*-{slug}.md")) if self.posts.exists() else []
        return [h for h in hits if re.fullmatch(rf"\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(slug)}", h.stem)]

    def state_of(self, list_name):
        key = norm(list_name)
        if key not in self.md_of:
            return "md없음"
        name, _ = self.md_of[key]
        if self.status.get(key, {}).get("layout_done"):
            return "완료"
        if self.status.get(key, {}).get("script_done"):
            return "레이아웃대기"
        if self.existing_post(slugify(name)):
            return "기존글있음"
        return "대기"

    def print_list(self):
        print(f"{'#':>2}  {'논문':<32}{'상태':<12}{'PDF':<5}카테고리")
        for i, n in enumerate(self.order, 1):
            key = norm(n)
            pdf = "O" if key in self.pdf_of else "-"
            print(f"{i:>2}  {n:<32}{self.state_of(n):<12}{pdf:<5}{self.sub_of.get(key, '??? 매핑없음')}")
        extra = [v[0] for k, v in self.md_of.items() if k not in [norm(n) for n in self.order]]
        if extra:
            print("\n리스트에 없는 md:", ", ".join(sorted(extra)))

    def next_pending(self, count):
        return [n for n in self.order if self.state_of(n) == "대기"][:count]

    def post_date(self, list_name):
        idx = [norm(n) for n in self.order].index(norm(list_name))
        now = datetime.now()
        d = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=idx + 1)
        if d >= now:  # 미래 날짜의 글은 Jekyll이 빌드에서 조용히 제외한다
            d -= timedelta(days=1)
        return d

    def convert(self, query, dry_run=False, force=False):
        key = norm(query)
        if key not in self.md_of:
            sys.exit(f"'{query}'에 해당하는 md를 찾지 못했습니다. --list로 이름을 확인하세요.")
        name, md_path = self.md_of[key]
        list_name = next((n for n in self.order if norm(n) == key), name)
        sub = self.sub_of.get(key)
        if not sub:
            sys.exit(f"'{name}'의 카테고리 매핑이 없습니다. CATEGORIES에 추가하세요.")
        slug, adir = slugify(name), safe_dir(name)
        existing = self.existing_post(slug)
        if existing and not force:
            print(f"[건너뜀] 이미 포스트가 있습니다: {existing[0].relative_to(self.repo)}")
            return
        date = self.post_date(list_name)
        post_path = self.posts / f"{date:%Y-%m-%d}-{slug}.md"
        report = {"images": [], "missing": [], "callouts": 0, "custom_emoji": []}

        body = md_path.read_text(encoding="utf-8")
        body = re.sub(r"\A\s*# .*\n+", "", body)
        body = self._migrate_images(body, name, slug, adir, dry_run, report)
        body = self._convert_callouts(body, report)  # 콜아웃 안의 커스텀 이모지는 여기서 대체 아이콘으로 바뀐다
        # 콜아웃 밖에 남은 커스텀 이모지: notion:// 내부 주소라 밖에서는 깨진 이미지가 되므로 걷어낸다
        body, stray = re.subn(r'^[ \t]*<img src="notion://[^>]*>[ \t]*\n', "", body, flags=re.M)
        report["custom_emoji"] += ["콜아웃 밖 → 제거"] * stray
        body = protect_inline_math(body)

        front = (f"---\ntitle: {name} 리뷰\ndate: {date:%Y-%m-%d %H:%M:%S} +0900\n"
                 f"categories: [AI Paper Reviews, {sub}]\nmath: true\n---\n\n")

        tag = "[dry-run] " if dry_run else ""
        print(f"{tag}{name}")
        print(f"  포스트   : {post_path.relative_to(self.repo)}")
        print(f"  카테고리 : AI Paper Reviews > {sub}")
        print(f"  날짜     : {date:%Y-%m-%d %H:%M}")
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
        self.posts.mkdir(parents=True, exist_ok=True)
        post_path.write_text(front + body.rstrip() + "\n", encoding="utf-8")
        self.status[key] = {"name": name, "post": str(post_path.relative_to(self.repo)),
                            "script_done": True, "layout_done": False,
                            "pdf": key in self.pdf_of,
                            "converted_at": datetime.now().isoformat(timespec="seconds")}
        self._save_status()

    def _migrate_images(self, body, name, slug, adir, dry_run, report):
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
            dest = self.assets / adir / fname
            resized = False
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                resized = self._shrink(dest)
            else:
                resized = self._width(src) > MAX_WIDTH
            report["images"].append((target, f"{adir}/{fname}", resized))
            if Path(alt).suffix.lower() in IMAGE_EXTS or not alt.strip():
                alt = f"{name} figure {counter}"
            return f"![{alt}](/assets/img/ai_paper_reviews/{adir}/{fname})"

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

    def mark_layout_done(self, query):
        key = norm(query)
        if key not in self.status:
            sys.exit(f"'{query}'는 아직 변환 기록이 없습니다.")
        self.status[key]["layout_done"] = True
        self._save_status()
        print(f"[완료 표시] {self.status[key]['name']}")

    def _save_status(self):
        self.status_file.write_text(json.dumps(self.status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    ap = argparse.ArgumentParser(description="노션 논문리뷰 export → Jekyll 포스트 변환")
    ap.add_argument("name", nargs="?", help="변환할 논문 이름")
    ap.add_argument("--list", action="store_true", help="전체 상태표")
    ap.add_argument("--next", type=int, metavar="N", help="다음 대기 논문 N편")
    ap.add_argument("--dry-run", action="store_true", help="쓰지 않고 계획만 출력")
    ap.add_argument("--force", action="store_true", help="기존 포스트가 있어도 덮어씀")
    ap.add_argument("--mark-layout-done", metavar="NAME", help="레이아웃 검수 완료 표시")
    args = ap.parse_args()

    mig = Migration(find_repo(Path(__file__).resolve().parent))
    if args.list:
        mig.print_list()
    elif args.next:
        print("\n".join(mig.next_pending(args.next)))
    elif args.mark_layout_done:
        mig.mark_layout_done(args.mark_layout_done)
    elif args.name:
        mig.convert(args.name, dry_run=args.dry_run, force=args.force)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
