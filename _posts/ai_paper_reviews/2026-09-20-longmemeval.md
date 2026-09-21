---
title: LongMemEval 리뷰
date: 2026-09-20 01:03:00 +0900
categories: [AI Paper Reviews, Memory & Personalization]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**LONGMEMEVAL: BENCHMARKING CHAT ASSISTANTS ON LONG-TERM INTERACTIVE MEMORY**<br>
Date: 2024.10.14<br>
Venue: ICLR 2025<br>
Author: Di Wu et al. (UCLA, Tencent AI lab)

</div>
</div>

## Motivation

![논문 Table 1: LongMemEval과 기존 장기 메모리 벤치마크(MSC, DuLeMon, MemoryBank, PerLTQA, LoCoMo, DialSim)의 도메인, 세션·질문 수, 컨텍스트 길이, 다루는 핵심 메모리 능력(IE, MR, KU, TR, ABS) 비교](/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig1.png)

기존의 메모리 벤치마크들은 인간-인간 간의 대화에만 포커스를 맞추고있음. 
근데 실제로는 인간-AI 대화를 해야하는데, 인간-인간 대화는 일상적인 잡담이나 감정교류나 대부분이라 task 부탁이나 뭔가를 물어보는 인간-AI 대화와는 성격이 좀 다름.
대화길이도 몇천토큰 수준의 고정된 길이라 한계가 있음.

## LongMemEval 개요

![논문 Figure 1: LongMemEval의 7가지 질문 유형 예시 - single-session-user, single-session-assistant, single-session-preference, temporal-reasoning, knowledge-update, multi-session, abstention](/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig2.png)

IE, MR, TR, ABS, KU 5가지 유형의 능력을 테스트하고, 총 500문제로 구성됨.
측정하는건 거의 LoCoMo와 동일하고, IE는 single-hop, MR은 multi-hop, TR은 temporal, ABS는 adversarial과 동일함.
사용자에 대한 지식을 동적으로 업데이트하는 KU task만 다른데 사실 LoCoMo도 다른 task들에 녹아 있었음.
다만, IE는 single-session-user, assistant, preference task로 나눠져서 task는 총 7종류임.

특이하게도, Dialogue가 있고 query(문제)가 주어지는 벤치마크들과 달리,  $$\text{Instance}=(\mathbf{S},q,t_q,a)$$  이런식으로 얘는 대화세션들과 문제와 정답들로 이루어진 조립세트형식임.
$$\mathbf{S}=[(t_1,S_1),(t_2,S_2),...,(t_N,S_N)]$$가 문제푸는데 필요한 세션들이라서, 중간에 쓸모없는 대화기록을 집어넣어서 전체 대화 길이를 원하는만큼 조정할 수 있음.
보통은 115k 컨텍스트 길이를 갖는 $$LongMemEval_S$$이랑 1.5M 컨텍스트 길이를 갖는 $$LongMemEval_M$$를 표준설정으로 사용.

## 인스턴스 생성 파이프라인

![논문 Figure 2: 데이터 생성 파이프라인 - (a) 사람이 질문과 증거 문장 작성, (b) 증거 세션을 LLM으로 시뮬레이션하고 사람이 수정, (c) 테스트 시 길이를 자유롭게 조절하는 대화 기록 구성](/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig3.png)

**질문 생성**

LoCoMo처럼 페르소나 시드를 만든다음 LLM을 통해 풍부한 사용자배경으로 합성함.
다만, LoCoMo의 페르소나와 달리 이건 인격이라기보단 인간에 대한 배경정보에 가까움.

```
Q: 나 악기 몇개 가지고있게? (+ 필요하다면 타임스탬프도)
A: 4
```

그 배경정보를 이용해서 LLM에 페르소나에 기반해서 질문-정답쌍들을 만들어보라고 했는데, 품질이 너무 나빠서 사실상 사람이 대부분 수작업 편집했고, 5%정도밖에 못살아남았다고 함.

**증거세션 합성**

```
증거1: 요즘 검은색 펜더 일렉기타를 엄청 치고있어
증거2: 야마하 어쿠스틱기타를 산지 벌써 8년이나 됐네
증거3: 오래된 펄 드럼 세트를 팔까 생각중이야
증거4: 내 코르그 피아노를 수리해줄 기사를 찾고있어
```

이제 $$q,a,(t_q)$$가 만들어졌으니 다음은 $$\mathbf{S}$$를 만들어야함.
이건 먼저 주석자가 사용자배경을 보고 수작업으로 근거문장을 발췌하고, 그 근거문장을 시드로 사용해서 각 세션들을 합성해냄.
LLM에 각 근거문장을 주고, 근거문장을 자연스럽게 드러내는 AI-인간 대화를 하라고 시킴.
그리고 이렇게 문제마다 만들어진 세션(최대 6개)의 품질을 위해 잘못된부분은 수동으로 편집하고, 필요한경우 타임스탬프도 추가해서 $$\mathbf{S}=[(t_1,S_1),(t_2,S_2),...,(t_N,S_N)]$$를 만들어냄.

**노이즈세션 추가**

이제 컨텍스트 길이를 뻥튀기시키기 위해 노이즈 대화세션들을 섞는데, ShareGPT나 UltraChat같은 외부 데이터셋을 사용하기도 하고, 자기들이 다른 인스턴스에서 합성해놓은 증거세션도 지금 문제랑 충돌하지 않는애들을 노이즈 세션으로 사용함.
길이는 자유롭게 뻥튀기할수 있지만, 약 50세션의 115k 컨텍스트 길이를 갖는 $$LongMemEval_S$$이랑 500세션의1.5M 컨텍스트 길이를 갖는 $$LongMemEval_M$$를 표준설정으로 사용.
각 세션은 평균 2500토큰, 10라운드이내인듯.

## **평가 메트릭**

- 시뮬레이션

이 논문은 인덱싱→검색→응답생성 순서로 작동하는 메모리모델을 상정하고 만든 벤치마크이기 때문에, 응답뿐 아니라 검색도 평가함.
응답은 LLM-as-judge방식으로 모델의 응답이 맞았는지 yes/no 이진평가하고, 검색이 제대로 됐는지는 대화속에 숨겨진 실제 증거문장과 검색된 문장의 Recall@k, NDCG@k을 통해 메트릭으로 사용함.
NDCG는 golden(증거세션들)을 검색해올때 순위까지 반영하는 방식

<details markdown="1">
<summary>Recall@5, NDCG@5 예시</summary>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>💡</div>
<div markdown="1" style="flex:1; min-width:0;">

쿼리: 내가 가장 최근에 가족여행으로 다녀온곳이 어디였지?<br>
실제 golden 증거세션: ES1, ES2

검색결과<br>
R1: 쓸데없는 잡담 (관련도 0)<br>
R2: ES1 (관련도 1)<br>
R3: ES2 (관련도 1)<br>
R4: 쓸데없는 잡담 (관련도 0)<br>
R5: 쓸데없는 잡담 (관련도 0)<br>
$$Recall@5 = 2/2 = 1$$

$$DCG@5 =$$<br>
$$\sum \frac{관련도}{log_2(순위+1)}$$<br>
$$= 0/ \log_2(2)+1/ \log_2(3)+1/ \log_2(4)+0/ \log_2(5)+0/ \log_2(6)$$<br>
$$=1.13$$<br>
이상적으로 관련정보가 1,2등에 몰려있을때의 DCG, 즉 IDCG는<br>
$$IDCG@5=1/\log_2(2)+1/\log_2(3)=1.63$$<br>
DCG를 IDCG로 나눠서 정규화해서 NDCG를 구하면,<br>
$$NDCG=1.13/1.63=0.69$$

</div>
</div>

</details>


근데 Recall을 어떻게 구해서 맞는 메모리를 검색해왔는지 판단한다는거지? 했는데, 인스턴스마다 메타데이터가 달려있다고 함.
후술하겠지만, 메타데이터가 Gold set = {ES1-R1, ES2-R3, ES3-R2, ES4-R1} 이런식으로 세션뿐만 아니라 라운드까지 표시되어있어서, 나중에 세팅에 따라 Recall 기준을 어떻게 볼건지 정할 수 있음.

## 상업시스템

<div style="display:flex; gap:12px; align-items:flex-start;">
  <figure style="width:41%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig4.png" alt="논문 Figure 3 (a): 메모리 기능이 있는 상용 챗봇(ChatGPT, Coze)의 정확도 - Offline Reading 대비 큰 폭으로 하락" style="width:100%;">
  </figure>
  <figure style="width:57%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig5.png" alt="ChatGPT의 '저장된 메모리' 설정 화면 캡처" style="width:100%;">
  </figure>
</div>

메모리기능이 지원되는 상업모델(사실상 현존 최강모델)들이 진짜로 세션간 메모리를 잘 기억하는지 자기들 LongMemEval을 변형해서 테스트해봄.
LongMemEval의 길이를 3~6 세션으로 아주 짧게 단축한 형태를 사용했고, ChatGPT, Coze는 사용자 채팅은 똑같이 통제할수있지만 챗봇부분은 자기가 생성하므로 통제할수 없어 7가지 유형중 가능한 일부만 사용함.

offline reading은 메모리기능을 사용하지 않고 한 세션내에 대화기록을 전체 컨텍스트로 한방에 넣어주는 방식인데, 높은 성능을 보였음.
근데 세션단위로 새로운 세션을 파고 대화했을때는 세션 메모리를 지원하는 모델이었음에도 상당히 성능이 떨어지는것을 확인할 수 있었음.
심지어 원래 LongMemEval보다 훨~씬 쉬운 버전임에도 상용서비스가 미진한 성능을 보이는것을 보여 메모리 에이전트의 갈길이 멀다는점을 어필함.

<figure style="width:56%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig6.png" alt="논문 Figure 3 (b): long-context LLM들의 Oracle 대비 LongMemEval_S 정확도 하락 (Chain-of-Note 유무)" style="width:100%;">
</figure>

그리고 사실 offline으로 한번에 때려넣는것도 LongMemEval_s만 하더라도 컨텍스트가 길어지니까 성능이 확 떨어져서, long-context능력을 기른다고 될일이 아니고 결국 메모리를 쓰는 방향으로 가야되는건 맞음.

## 메모리시스템 제안

![논문 Figure 4: 장기 메모리 챗봇의 통합 구조 - (1) Indexing, (2) Retrieval, (3) Reading 세 단계와 네 개의 control point(CP1 Value, CP2 Key, CP3 Query, CP4 Reading Strategy)](/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig7.png)

먼저, 문제 공식화를 위해메모리를 사용하는 챗봇시스템을 indexing, retrieval, reading 3단계로 분류하고, 메모리 시스템은  $$[(k_1,v_1),(k_2,v_2),...]$$ 이런식의 데이터저장소라고 공식화함.
query가 들어오면 key로 조회해서 value를 꺼내오는 방식

메모리 시스템을 개선하기위해 제어지점구성요소(CP) value, key, query, reading strategy 부위별로 분석함.
다만, Mem0나 다른 메모리 방법론들처럼 메모리 관리방법이 있는건 아니고 그냥 모든 대화데이터 다 무지성 추가 방식으로 하는듯.

#### **CP1: Value**

<figure style="width:78%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig8.png" alt="논문 Figure 11: 인덱싱용 정보를 뽑는 zero-shot 프롬프트 - Summaries, Keyphrases, User Facts" style="width:100%;">
</figure>

세션을 통째로 저장할건지, 라운드단위로 저장할건지, 요약,사실등으로 압축할건지 비교.
Llama3.1-8B-Instruct로 한다고 함.

![논문 Figure 5: value 설계(Session, Round, Session Summary, Session Facts, Round Facts)에 따른 LongMemEval_M QA 정확도 - Reader가 GPT-4o일 때와 Llama 3.1 8B Instruct일 때](/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig9.png)

근데 논문에서 주장한것과 달리 실제데이터는 보면 round나 sessiond이나 큰 성능차이가 나지는 않고, facts처럼 압축된부분의 실제 예시가 없어서 명확히는 확인 불가능
근데 프롬프트만 봤을때는 그냥 압축을 제대로 안해서 성능이 별로 안나오는거지, 저자들 주장처럼 압축하는 방법 자체가 구린건 아닌것같음.

#### **CP2: Key**

value를 통째로 key로 사용하는건 비효율적임.
그리고 value가 raw 세션이 아니라 압축되거나 쪼개진 형태라고 해도, 여전히 군더더기가 있으므로 key는 value와 별도로 더 핵심적이거나 변별력있는 정보를 사용하는게 좋을것이라고 생각하고 여러 조합을 실험

![논문 Table 3: key 설계에 따른 LongMemEval_M의 검색(Recall, NDCG) 및 end-to-end QA 성능 - K = V + fact가 가장 좋음](/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig10.png)

그 결과, key로 다른 선택지들을 사용하는건 value를 key로 갖다쓰는것보다 성능이 안좋게나왔고, fact까지 같이 붙여서 쓰는게 조금 더 좋게나옴.
value를 통째로 검색대상으로 쓰는게 비효율적일거라는 생각에서 key를 따로 둔다는 생각이 나왔을것같은데, 정작 value보다 key가 더 비대해지는게 아이러니하고 모순적인듯.

#### **CP3: Query**

```
질문 날짜: 2023/04/27
질문: "Which airline did I fly with the most 
      in March and April?"
→ LLM 출력: {"start": "2023/03/01", "end": "2023/04/30"}
```

```
질문 날짜: 2023/06/25
질문: "How many months have passed since my last 
      museum visit with a friend?"
→ LLM 출력: {"start": "2023/01/01", "end": "2023/06/25"}
```

```
세션 날짜: 2023/05/15
유저 발화: "I'm thinking about my family trip to 
           Hawaii last month..."
→ LLM 출력: {"date": "2023/04/15", "event": "Family trip to Hawaii"}
```

query가 복잡(시간언급 등)하면 메모리 검색이 잘 안되므로 확장하는 방법 고려.
정확히는 확장이라기보다는 검색할 시간범위를 뽑아내서 검색할 문서 필터링할때 쓰는방식.
query뿐만 아니라 메모리 인덱스들도 상대적 시간표현을 실제 날짜로 변형해줘야함. 그래서 query를 가지고 문서를 검색할때, 아까 뽑은 시간 범위 안의 문서들에서만 검색을 진행하는 방식.

![논문 Table 4: temporal reasoning 부분집합에서 time-aware query expansion 유무에 따른 검색 성능](/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig11.png)

그렇게하면 성능이 조금 오르는데, 좋은모델로 확장을 해야지 Llama3.1-8B-Instruct를 쓰면 오히려 성능하락

#### **CP4: Reading strategy**

문서를 잘 검색해오는것과 좋은 응답을 생성하는것은 별개이므로, 검색된문서로 어떻게 응답을 생성할지 분석.
Oracle 설정으로 정답세션들을 다 주고 응답을 생성하게했는데 문제하나당 근거세션들이 4개정도라고 치면 1만토큰정도이고 10장정도의 분량이니 모델도 헷갈릴만 하고 형식에따라 점수가 다를 만 한듯.

![논문 Figure 6: oracle 검색 설정에서 읽기 전략(NL/JSON 형식 × Direct Prediction/Chain-of-Note)별 QA 정확도](/assets/img/ai_paper_reviews/LongMemEval/longmemeval-fig12.png)

Json형식으로 검색된 문서를 주고 CoN으로 문서에 대해 짧게 요약한뒤 응답을 생성하도록 하는방식이 유의미하게 성능이 더올랐음.
