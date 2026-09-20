---
name: paper-review-convert
description: 노션에서 export한 AI 논문리뷰(md + PDF)를 이 블로그의 Jekyll 포스트로 변환하는 마이그레이션 스킬. 사용자가 논문리뷰 변환, 마이그레이션, "다음 5편", "논문 옮겨줘", 노션 export 처리, blog_source의 논문 작업을 언급하면 반드시 이 스킬을 사용할 것. 개별 논문 이름을 대며 포스트로 만들어 달라고 할 때도 해당된다.
---

# 논문리뷰 변환 스킬

노션 export(md + 이미지 + PDF)를 블로그 포스트로 옮긴다. 기계적인 부분은 스크립트가, 눈으로 봐야 하는 부분(레이아웃)은 네가 한다. 골든 샘플은 `_posts/ai_paper_reviews/2026-09-18-vgg.md` — 결과물이 이 글과 같은 수준·형식이면 성공이다.

## 자료 위치

- 원본: `blog_source/논문리뷰 마이그레이션/` (md + 이미지 폴더), PDF는 그 안의 `pdf/`
- 순서·카테고리 기준: `blog_source/논문리스트.txt`, `blog_source/카테고리매핑.md`
- 진행상황: `blog_source/migration_status.json` (스크립트가 관리)
- 스크립트: 이 스킬 폴더의 `scripts/convert_notion.py`

## 작업 절차

한 번 호출에 **5편**이 기본 단위다 (사용자가 다른 수나 특정 논문을 지정하면 그에 따른다).

### 1. 대상 선정

```bash
python3 .claude/skills/paper-review-convert/scripts/convert_notion.py --next 5
```

PDF가 없는 논문이 걸리면 변환하지 말고 사용자에게 알린다. PDF 없이는 원본 레이아웃을 알 수 없어서 이 스킬의 핵심 단계를 수행할 수 없다.

### 2. 편마다: 스크립트 변환

```bash
python3 .claude/skills/paper-review-convert/scripts/convert_notion.py "논문명"
```

스크립트가 하는 일: 포스트 파일 생성, front matter 부착, 이미지 복사·리네임·축소, 이미지 경로 치환, `<aside>` 콜아웃을 노션 스타일 HTML로 변환. 출력의 경고(파일 없음 등)를 확인한다. 이미 포스트가 있는 논문은 스크립트가 알아서 건너뛴다 — 기존 글은 덮어쓰지 않는다.

### 3. 편마다: PDF를 보고 레이아웃 설계 (이 스킬의 핵심)

md export는 노션의 단 배치와 이미지 크기 정보를 잃는다. PDF가 그 정보의 유일한 출처다. **포스트를 수정하기 전에 PDF 전체를 먼저 읽고** 다음을 파악한다:

- 나란히 배치된 이미지 묶음 (2장, 3장…)과 대략의 폭 비율
- 전체 폭이 아닌 이미지 (가운데 정렬된 작은 그림 등)와 그 크기
- 이미지 캡션 (md에서는 이미지 바로 다음 줄의 평범한 텍스트로 나온다)

그다음 포스트의 해당 이미지들을 아래 패턴으로 바꾼다. 전체 폭 + 캡션 없는 이미지는 마크다운 `![]()` 그대로 둔다.

**나란히 배치** (폭은 PDF의 비율을 %로, 합계 98~99%):

```html
<div style="display:flex; gap:12px; align-items:flex-start;">
  <figure style="width:49%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/X/x-fig1.png" alt="설명" style="width:100%;">
    <figcaption style="text-align:center; font-size:0.85em; color:gray;">
      캡션
    </figcaption>
  </figure>
  <figure style="width:49%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/X/x-fig2.png" alt="설명" style="width:100%;">
  </figure>
</div>
```

**단독 이미지 (축소 또는 캡션 있음)**:

```html
<figure style="width:60%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/X/x-fig3.png" alt="설명" style="width:100%;">
  <figcaption style="text-align:center; font-size:0.85em; color:gray;">
    캡션
  </figcaption>
</figure>
```

**토글 블록** (PDF에 ▼로 보이는 것; md에서는 들여쓴 내용이 딸린 `- 목록 항목`으로 나오며 스크립트가 "토글 의심"으로 알려준다):

```html
<details markdown="1">
<summary>토글 제목</summary>

안쪽 내용은 들여쓰기를 없애고 쓴다.<br>
여기는 HTML 블록 안쪽이라 줄바꿈에 br이 필요하다.

</details>
```

**그림 + 텍스트 2단 구성** (노션 단 나누기로 그림 옆에 글을 둔 경우):

```html
<div style="display:flex; gap:16px; align-items:flex-start;">
  <figure style="width:35%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/X/x-fig1.png" alt="설명" style="width:100%;">
  </figure>
<div markdown="1" style="width:63%;">

오른쪽 칸의 글.<br>
이 안의 이미지는 마크다운 `![]()`으로 써도 된다 (flex의 직접 자식이 아니므로).

</div>
</div>
```

`markdown="1"` 요소의 여는 태그와 닫는 태그는 위처럼 **줄 맨 앞에 붙여 쓴다** (들여쓰지 않는다). 이유는 아래 규칙 목록 참고.

md export가 캡션을 통째로 빠뜨리는 경우가 있다 (특히 링크가 든 캡션). PDF에 캡션이 보이는데 md에 없으면 PDF의 문구 그대로 복원한다.

캡션이 없으면 `<figcaption>` 블록은 생략한다. 캡션을 figcaption으로 옮겼으면 본문에 남은 원래 캡션 줄은 지운다 (중복 방지). alt 텍스트는 그림 내용을 짧게 설명하도록 다듬는다.

이 구조를 지켜야 하는 이유: 테마가 빌드 시 모든 `<img>`를 확대용 `<a>`로 감싼다. 이미지가 flex 컨테이너의 직접 자식이면 그 `<a>`가 자식 자리를 차지해 폭 지정이 무너진다. 폭은 항상 내가 만든 `<figure>`가 갖고, `<img>`는 `width:100%`만 갖게 한다.

### 4. 편마다: 본문 검수

- 노션 잔재: 깨진 블록, 의미 없는 노션 내부 링크(`notion.so/...`), 빈 제목 등을 정리한다.
- 수식: 스크립트가 인라인 `$...$`를 `$$...$$`로 바꿔 둔다. 이 블로그의 엔진(kramdown)은 한 겹 `$`를 수식으로 인식하지 못해 내부의 `\{`를 `{`로, `\\`를 `\`로 망가뜨리기 때문이다 (`$$...$$`는 문장 중간에 있으면 인라인 수식으로 보호된다). 그래도 변환되지 않고 남은 한 겹 `$`나 짝이 안 맞는 `$$`가 없는지 훑어본다. 직접 수식을 고칠 때도 한 겹 `$`는 쓰지 않는다.
- 유튜브 링크가 핵심 자료면 iframe으로 임베드한다: `<iframe src="https://www.youtube.com/embed/ID" style="width:100%; aspect-ratio:16/9; border:0;" allowfullscreen></iframe>`
- 내용(문장)은 고치지 않는다. 사용자가 쓴 리뷰의 말투와 내용은 그대로 보존한다. 오탈자를 발견해도 임의로 고치지 말고 보고만 한다.

검수까지 끝나면 표시한다:

```bash
python3 .claude/skills/paper-review-convert/scripts/convert_notion.py --mark-layout-done "논문명"
```

### 5. 배치 끝: 무결성 검증

```bash
export PATH="/opt/homebrew/opt/ruby@3.4/bin:$PATH" SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX26.sdk && tools/test.sh
python3 .claude/skills/paper-review-convert/scripts/audit_build.py
```

두 검사는 보는 것이 다르다. `tools/test.sh`는 깨진 링크만 본다. `audit_build.py`는 빌드된 HTML에서 **마크다운이 처리되지 않은 흔적**(글자로 노출된 `</div>`, 안 바뀐 `$$`·`## `·`![]()`, 중복 `<br>`)을 찾는다 — HTML 블록 하나가 안 닫혀서 그 뒤 문서 전체가 날것으로 나가는 사고는 test.sh를 그대로 통과하기 때문에 이 검사가 반드시 필요하다. 반드시 test.sh(빌드) 뒤에 실행한다.

"특정 문자열이 결과물에 있는지"만 확인하고 통과라고 판단하지 않는다. 그런 검사는 페이지의 나머지가 망가져도 통과한다.

실패하면 원인을 찾아 고치고 다시 돌린다. 고칠 수 없으면 실패 내용을 그대로 보고한다.

### 6. 멈추고 보고

배치가 끝나면 **반드시 멈춘다.** 다음을 보고한다:

- 변환한 논문과 각 포스트 경로
- 편별 레이아웃 결정 (어떤 이미지를 나란히 놓았는지, 비율)
- 애매했던 판단, 발견한 오탈자, 경고
- test.sh 결과

사용자가 `tools/run.sh`로 직접 확인한 뒤 커밋·푸시한다. **git add/commit/push는 절대 하지 않는다** — 이 프로젝트에서 외부로 나가는 행동은 전부 사용자 몫이다. 다음 배치는 사용자가 다시 요청할 때 시작한다.

## 이 블로그의 규칙 (어기면 실제로 사고가 났던 것들)

- **표준 문법만**: Chirpy 전용 문법(`{: .prompt-tip }`, `{% include embed/... %}`)은 쓰지 않는다. 테마를 바꿔도 글이 살아남아야 한다. 본문은 마크다운, 마크다운으로 안 되는 것(병렬 이미지, 콜아웃 박스)만 인라인 스타일 HTML.
- **태그 미사용**: front matter에 `tags`를 넣지 않는다. 태그가 하나라도 생기면 태그 페이지가 생성되고, 삭제된 `/tags/` 목록 페이지를 링크해서 빌드 검사가 실패한다.
- **HTML 블록 앞뒤에는 빈 줄**: 빈 줄 없이 붙이면 뒤따르는 마크다운이 HTML 블록에 빨려 들어가 렌더링되지 않는다.
- **HTML 블록 안의 마크다운**: `markdown="1"` 속성이 있는 요소 안에서만 처리된다 (콜아웃 템플릿 참고). 안쪽 내용은 4칸 이상 들여쓰지 않는다 (코드블록이 된다).
- **`markdown="1"` 요소의 닫는 태그를 들여쓰지 않는다**: 안쪽 내용이 목록으로 끝나는데 닫는 태그가 `  </div>`처럼 들여써져 있으면, kramdown이 그 줄을 마지막 목록 항목의 이어지는 내용으로 삼켜서 글자 그대로 출력한다. 블록이 닫히지 않으므로 **그 뒤 문서 전체가 마크다운 처리 없이 날것으로 나간다** (제목은 `## `, 수식은 `$$`, 이미지는 `![]()` 그대로). BatchNorm 글에서 "느낀점" 콜아웃이 불릿 목록으로 끝나면서 실제로 발생했고, test.sh는 이걸 잡지 못했다. 여는·닫는 태그 모두 줄 맨 앞에 쓴다.
- **줄바꿈 `<br>`은 위치에 따라 정반대다**: `_config.yml`에 `kramdown.hard_wrap: true`가 켜져 있어 **일반 본문**에서는 엔터 한 번이 그대로 줄바꿈으로 렌더링된다. 여기에 `<br>`을 더하면 줄바꿈이 두 번 들어가므로 넣지 않는다. 반면 **`markdown="1"` HTML 블록 안쪽**(콜아웃, `<details>`, 2단 구성의 텍스트 칸)에는 hard_wrap이 닿지 않아서, 줄 단위로 끊으려면 줄 끝에 `<br>`을 직접 붙여야 한다 (문단의 마지막 줄 제외). 콜아웃은 스크립트가 처리하지만, 직접 만드는 블록은 네가 챙긴다. 두 경우 모두 실제 빌드 결과로 검증된 동작이다.
- **미래 날짜 금지**: `date`가 빌드 시점보다 미래면 글이 조용히 누락된다. 스크립트가 보정하지만 직접 고칠 때 주의한다.
- **카테고리명은 매핑표와 글자 하나까지 동일하게**: 오타는 새 카테고리를 만든다.
