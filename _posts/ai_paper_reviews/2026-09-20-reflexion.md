---
title: Reflexion 리뷰
date: 2026-09-20 00:52:00 +0900
categories: [AI Paper Reviews, Agents]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Reflexion: Language Agents with Verbal Reinforcement Learning**<br>
Date: 2023.3.20<br>
Venue: NeurIPS 2023<br>
Notable author: Karthik Narasimhan<br>
Comprehension: 3단계

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>😲</div>
<div markdown="1" style="flex:1; min-width:0;">

**느낀점**<br>
좋은 방법인데 HotPotQA같은데서는 다음문제로 가면 반성을 통해 학습한게 무용지물이 됨.<br>
그리고 task별로 Evaluator가 맞춤설계되어야해서 범용성이 없는듯…

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>🦅</div>
<div markdown="1" style="flex:1; min-width:0;">

**전체적인 view**<br>
기존의 강화학습은 무식한 브루트포스 탐색처럼 행동중에 범인을 찾아나갔는데, 데이터 비효율적일뿐 아니라 파라미터 수정도 너무 비싸서 쓰기 힘듦.<br>
그래서 기존 경험을 분석한걸 넣어서 in-context learning으로 정책을 바꾸는 언어적 강화학습을 만듦.<br>
**실행 flow**<br>
input이 들어오면<br>
Actor모델이 종합적인 상태와 reflection까지 받아 한 에피소드를 실행하고 trajectory 반환.<br>
그 trajectory를 보고 task별 맞춤 Evaluator가 내부평가를 수행함(실제 평가와 다를수있음).<br>
그럼 Self-consistency모델이 반성 수행하고 회고 반환.

</div>
</div>

## 0. Abstraction

딱 이 시점이 LLM으로 다양한 작업을 하는 agent를 본격적으로 만들어보기 시작한 타이밍인데, agent를 만들때 RL을 사용하면 좋을 것 같지만 전통적인 RL은 fine-tuning을 해야하고 데이터효율도 낮기때문에 쓰기 어렵다함.

RL은 직접 rollout을 통해 샘플들을 벌어와야하는데, 설상가상으로 agent task의 경우 보통 여러 step으로 이루어져있고 보상으로도 보통 sparse reward를 사용하기때문에 잘못한 action에 대해 정확히 학습신호가 들어가기 어렵다고 함.

그래서 자기들은 피드백 신호를 받았을때 그걸로 모델의 parameter를 직접 fine-tuning하는건 아니지만 기억버퍼를 이용해 일종의 언어적인 RL을 구현함.

---

## 1. Introduction

ReAct, SayCan같은 기존의 agent연구들은 거대한 모델에 의존하기때문에 fine-tuning을 하기 너무 부담스러워서 보통 in-context learning에 많이 의존함.
그런데 in-context learning은 사실 새로운것을 배우는 과정이 결여되어있음…

![논문 Figure 1: Reflexion이 decision making, programming, reasoning task에서 동작하는 예시 - Task, Trajectory, Evaluation, Reflection, Next Trajectory 단계](/assets/img/ai_paper_reviews/Reflexion/reflexion-fig1.png)

그래서 저자들은 RL과 in-context learning의 장점을 잘 교접해서 Reflexion이라는 방법론을 만들어냄.
한마디로 언어적 강화학습 방법이라고 할 수 있고, 환경으로부터 얻은 피드백을 보고 언어적 gradient로 만들어내서 in-context로 들어갈 shot을 업데이트하는 방식임.

이 Reflexion을 사용하면 RL에 비해 훨씬 가볍고, 구체적인 피드백으로 정교한 학습신호를 주면서도 높은 explainability를 갖는다는 좋은 장점이 생김.

그렇게 만든 Reflexion은 원래 상정한 long-horizon task뿐 아니라 단일스텝 추론, 프로그래밍과제에서도 상당한 성능향상이 있었다고 함.

---

## 2. Related work

![논문의 관련 연구 비교표: reasoning·decision making 분야(Self-refine, Beam search)와 programming 분야(AlphaCode, CodeT, Self-debugging, CodeRL) 대비 Reflexion의 기능](/assets/img/ai_paper_reviews/Reflexion/reflexion-fig2.png)

self-refine은 이름은 비슷하지만 단일 생성작업에 맞춰져있고 실패로부터 배울수가 없음.
beam search도 훌륭하지만 최적의 답을 찾는 전략이지 실패로부터 배우는건 아님.

---

## 3. Reflexion: reinforcement via verbal reflection

![논문 Figure 2: (a) Reflexion 구조도 - Actor, Evaluator, Self-reflection과 단기·장기 기억, (b) Reflexion 강화 알고리즘 의사코드](/assets/img/ai_paper_reviews/Reflexion/reflexion-fig3.png)

Reflexion에는 3가지 모델을 사용함

**Actor $$M_a$$:** 
프롬프팅된 LLM.
관찰 $$o_t$$과 단기기억 $$\tau_{t}$$, 장기기억 $$mem$$을 입력받아 행동 $$a_t$$을 생성함.
단기기억 $$\tau_t$$는 뭐고 Actor에 왜 주는건지 의아했었는데, 이전 step까지의 trajectory를 의미하는거라고 함. 
직전 스텝까지의 trajectory를 사용하는건 여러 step으로 구성된 agentic task를 다룬다면 누구나 다 사용하는 당연한거임.
장기기억 $$mem$$은 실패한 에피소드마다 하나씩 생성되는데, 무한히 쌓아놓을수 없으니 $$\Omega$$개만 버퍼에 남겨두고 오래된건 지움. 보통 1~3개정도만 남겨둔다고 함. 

**Evaluator $$M_e$$:** 
내부적인 채점을 수행하는 주체.
Actor가 생성한 궤적 $$\tau_t$$를 채점하고 보상점수 $$r_t$$ 반환.
언어공간에서 채점은 명확히 정의하기가 어려워서 각 작업마다 다르게 채점한다고 함.
가령 추론 task에서는 정확히 정답과 일치하는지, 의사결정에서는 규칙기반 휴리스틱으로, 또 어떤곳에서는 LLM as a judge라서 다른 두놈과 달리 LLM이 아닐수도 있음

**Self-Reflection $$M_{sr}$$:** 
프롬프팅된 LLM.
궤적 $$\tau_t$$, 보상 $$r_t$$, 장기기억 $$mem$$를 입력받아 언어적 gradient $$sr_t$$로 바꿔줌.
Evaluator로 부터 나온 보상은 그냥 결과만 알려주지만, $$M_{sr}$$은 언어모델이기때문에 어떤 행동 $$a_i$$가 잘못되었는지 추론해낼 수 있고 구체적인 대안까지 제시함.

---

## 4. Experiments

### 4.1 Sequential decision making: ALFWorld

![논문 Figure 3: (a) 134개 ALFWorld task에서 trial 수에 따른 누적 성공률, (b) 실패 원인(hallucination, inefficient planning)별 trajectory 비율](/assets/img/ai_paper_reviews/Reflexion/reflexion-fig4.png)

ALFWorld에서 실험해보니, 베이스라인으로 사용한 ReAct only는 점수가 조금 오르다가 금방 plateau 되었지만  ReAct + Reflexion은 포화되지 않고 계속 향상되는것을 확인할 수 있음.

정성적으로 실패모드를 분석해보면, ReAct only에서는 아이템을 소지하고있지도 않은데 자기가 가지고있다고 착각하고 계속 상호작용하다가 나중에 어디서부터 잘못됐는지 감도 못잡는경우가 많았지만 Reflexion의 경우에는 이런 실패를 쉽게 식별하고 해결해나간다고 함.

### 4.2 Reasoning: HotpotQA

![논문 Figure 4: HotPotQA에서 (a) Reflexion ReAct 대 CoT, (b) CoT(GT) 추론, (c) episodic memory ablation 결과](/assets/img/ai_paper_reviews/Reflexion/reflexion-fig5.png)

HotpotQA에서도 Reflexion은 성능이 유의미하게 향상된 데 반해 베이스라인인 CoT는 아무리 반복해서 풀게 해도 매번 똑같은 방식으로 틀리고 개선이 되지 않았다고 함.
그래서 혹시 self-reflection이 아니라 데이터 누적때문인지 CoT에도 trajectory를 저장하는 Episodic memory(EPM)을 달아줬는데, 확실히 나아지긴 했지만 여전히 Reflexion에 밀림/

근데 ALFWorld와는 다르게 여기서는 다음문제로 가면 바로 무용지물이 되어서 가치가 상당히 퇴색되는것같음

### 4.3 Programming

![논문 Table 1: HumanEval, MBPP, Leetcode Hard에서 기존 SOTA와 Reflexion의 Pass@1 정확도](/assets/img/ai_paper_reviews/Reflexion/reflexion-fig6.png)

결과를 보면 기존의 SOTA를 유의미하게 눌러버린게 보임.
여기서는 내부채점을 할때 자기가 만든 테스트코드를 실행하는 방식을 사용함.
Actor가 코드를 생성하고 맞는지 테스트하기 위한 테스트코드까지 작성한 후, Evaluator라는 컴파일러에서 실행하는방식으로 내부평가함.

물론 Actor가 만든 테스트코드를 문법적으로 필터링해서 n개의 테스트코드를 뽑아내지만, 쓰레기같은 테스트케이스를 만드는 경우가 꽤 있다고 함.
HumanEval에서는 테스트코드를 잘 만들어냈지만, MBPP(python)에서는 별로 성능이 나오지않은게 보이는데, 아니 둘다 비슷비슷한 문제인데 왜 저런 차이가 나지? 싶었음.
근데 실패모드를 분석해보니까 저 차이가 테스트케이스를 쓰레기같은걸 만들어내는바람에 생기는거라고 함.
MBPP문제가 시간에 따라 변하거나 네트워크가 필요하거나 환경과 관련된것들이 있어서 테스트케이스를 짜는게 어려운경우가 많은데 이때 쓰레기테스트케이스가 만들어지는듯.

---

## 5. ~ 8.

Reflexion도 Local minima에 갇혀서 빠져나오지 못하는 경우가 있고, 현재는 최근 경험 몇개만 기억하는 Sliding window라서 기억력에 한계가 있다고 함.
