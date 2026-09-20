---
title: FocusAgent 리뷰
date: 2026-09-20 01:04:00 +0900
categories: [AI Paper Reviews, Agents]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**FOCUSAGENT: Simple Yet Effective Ways of Trimming the Large Context of Web Agents**<br>
Date: 2025.10.3<br>
Venue: LLA 2026 (ICLR workshop)<br>
Author: Imene Kerboua

</div>
</div>

## Motivation

웹을 조작하는 웹 에이전트가 observation으로 보통 AxTrees(접근성트리), DOM, 스크린샷을 쓰는데, AxTree는 DOM에 비하면 10배 이상 슬림하지만 이것마저도 수만토큰이 될정도로 너무 방대함.
그리고 실제로 작업에 필요한건 그중 아주 일부라서 이게 상당히 비효율적이라는거임.

그래서 Mind2Web이나 WebLINX같은 논문에서는 DOM을 청킹하고, query를 보고 필요한 청크만 검색해서 넣어주는 방법을 사용했음.
근데 이렇게하면 관련청크가 피상적으로 검색돼서 진짜 필요한 정보를 빼먹을수 있다고 함.
그리고 프롬프트 인젝션같은 보안위험도 어필하는데, 일단 이건 내 관심대상이 아니라 자세히 안봄.

## FocusAgent

![논문 Figure 2: FocusAgent의 retrieval 동작 - (1) AxTree에 줄 번호 부여, (2) LLM retriever가 CoT와 함께 관련 줄 범위 선택, (3) 나머지를 잘라내 AxTree 토큰을 61% 줄임](/assets/img/ai_paper_reviews/FocusAgent/focusagent-fig1.png)

단순히 prunning용 소형 LLM에 어딜 잘라낼지 정하게해서 토큰을 줄이는 방법임.
