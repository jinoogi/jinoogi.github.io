---
title: Web Agent with World Models 리뷰
date: 2026-09-20 00:48:00 +0900
categories: [AI Paper Reviews, Agents]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Web Agents with World Models: Learning and Leveraging Environment Dynamics in Web Navigation**<br>
Date : 2024.10.17<br>
Venue : ICLR 2025 Poster<br>
Notable Author : Hyungjoo Chae et al (Lang AGI + DLI lab )<br>
Comprehension : 3단계

</div>
</div>

## 0. Abstract

에이전트를 구축하는데 LLM을 보통 많이 사용해오고있음.
에이전트를 구축하는데 LLM을 많이 사용하는데, 기존의 LLM들은 환경에 대한 지식(world model) 없이 그냥 단어를 auto-regressive하게 패턴을 예측하는 방식이라 환불불가능한 항공권을 계속 구매한다던지 하는 사람이라면 절대 안할 이상한짓도 많이하고, task가 long-horizon인 경우도 확률론적으로 패턴을 예측하는방식은 점점 현실과 괴리가 누적되기때문에 잘 못한다고 함.
그래서 저자는 LLM에 world model을 입혀줘서 생각없이 그냥 패턴 따라하는게 아니라 자신의 행동이 어떻게 환경에 영향을 줄지 예측하면서 작동할 수 있는 월드모델 증강 에이전트(WMA)를 제안함.

근데 웹 에이전트인만큼 HTML 전체를 상태 $$s$$로 사용하면 너무 크고 비효율적이라 이전상태와의 변화를 자연어로 서술하는 전이중심 관측 추상화를 도입했음.
그렇게 완성된 WMA는 추가학습없이도 바로 좋은 성능을 보였다고 함.

---

## 1. Introduction

WebArena같은 웹 네비게이션 task에서는 인간 성공률은 78%정도인데 GPT-4 에이전트는 14.4%로 당시 프론티어 모델을 썼음에도 WebArena같은 웹 네비게이션 task에서는 성능이 처참했다고 함.
인간은 행동을 수행하기전에 결과를 예상할 수 있는 능력이 있고 이런 인식을 world model이라고 하는데, 기존의 LLM들은 이런 능력이 상당히 부족하다는걸 밝혀냈음.

저자들은 웹 도메인에 맞게 효율적으로 상태 $$s$$를 표현하는 전이중심관측 추상화라는 방법을 고안했고, 그렇게 효율적으로 world model을 학습시킴.
이제 이렇게 학습된 world model로 행동을 고를때 결과를 미리 예상하고 선택하는방식으로 추론을 수행하는 에이전트 WMA 완성!

아니 어떤 행동이 좋을지 예상하고싶은거면 model free로 $$Q(s,a)$$를 예상하게 학습시키면 되는거 아닌가? 했는데, 이렇게하면 환경이 조금이라도 바뀌면 바보가 된다고 함.
웹 환경은 자주 바뀌기때문에 **추상적인 인과관계**를 학습하는 world model 사용에 당위성이 생기는듯

---

## 2. Related work

웹 네비게이션 분야의 연구흐름으로는, 프론티어 LLM들이 대부분 closed model이기때문에 훈련을 하지 않는 방향으로 발전해왔다고 함.
크게 성공궤적데이터를 캐싱하는 계열과(Wilbur, AWM), 여러 경로를 탐색하는 일종의 test-time scaling 계열(AutoEval, Tree Search agent)로 분류할 수 있는데, 성공궤적을 저장하는 계열은 성공한 케이스에만 사용할 수 있고 일반화가 안된다는 단점이 있고, 경로탐색계열은 패턴을 따르는 방식이라 앞서말한 인간이라면 하지 않을 실수를 하거나 long horizon에서 성능이 하락하고, 너무 비싸다는 단점이 있음.

---

## 3. Preliminary analyses: Are current LLMs aware of environment dynamics in web navigation?

여기서는 LLM이 자신의 행동이 환경에 어떤 영향을 줄지 인식할 수 있는지?
world model을 통해 영향을 예측할 수 있다면 그걸 이용해서 최적의 행동을 선택할 수 있는지?
두가지를 검증함.

### 3.1 Preliminary analysis 1 - LLMS struggle with predicting the next states caused by their actions

<div style="display:flex; gap:12px; align-items:center;">
  <figure style="width:49%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig1.png" alt="논문 Figure 8: preliminary analysis 1에 쓰인 사람용 annotation 인터페이스 - 현재 관측과 행동을 보고 다음 상태 후보 중 하나를 고르는 화면" style="width:100%;">
  </figure>
  <figure style="width:49%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig2.png" alt="논문 Figure 1: 다음 상태 예측에서 LLM들의 정확도(52~58%)와 사람(83%) 비교" style="width:100%;">
  </figure>
</div>

LLM이 자기 행동의 결과를 예측할 수 있는지 확인하는 실험을 진행함.
이진분류문제로 변환해서 특정 행동을 했을때 다음 화면이 어떤상태일지 맞추게 했는데, 충격적이게도 50%대가 나왔음.
이진분류에서 50%대가 나왔다는건 사실상 찍기라는 이야기고, 모델이 미래에 대한 예측을 전혀 못한다는 말…

### 3.2 Preliminary analysis 2 - LLMS make better action selection when accessing the outcome of each action candidate

<figure style="width:56%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig3.png" alt="논문 Figure 2: 다음 상태 정보 유무에 따른 LLM들의 행동 선택 정확도" style="width:100%;">
</figure>

그러면 LLM가 미래를 예측할수 있는 능력이 있다면 성능이 올라가는지 검증해봤음.
10시선다로 올바른 행동을 선택하도록 했는데, 성능이 20%p씩 올랐음…
미래를 예측할수 있다면 기존 LLM도 얼마든지 더 좋은 퍼포먼스를 보일 수 있다는걸 증명

---

## 4. World Model Augmented web agents

![논문 Figure 3: 프레임워크 개요 - 위쪽은 world model 학습 3단계, 아래쪽은 world model을 이용한 추론 시 정책 최적화](/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig4.png)

웹 에이전트의 환경은 화면에 표시된 영역만 볼 수 있으므로, POMDP로 모델링함.
그래서 관측공간 $$\mathcal{O}$$와 상태공간 $$\mathcal{S}$$가 따로 있음.

### 4.1 World Model Training

**4.1.1 Step1: Harvesting agent-environment interaction data**

사용자 Instruction $$I$$가 주어졌을때의 trajectory $$\tau=\{o_1,a_1,o_2,...,a_n,o_{n+1}\}$$ 를 수집해서 데이터셋 $$\mathcal{D}=\sum_{t=1}^n\{I,o_t,a_t,o_{t+1}\}$$를 구성함.

**4.1.2 Step2: Transition focused observation abstraction**

직관적으로는 world model을 $$\text{Model}(o_t)\rightarrow o_{t+1}$$를 예측하도록 하면 될 것 같지만, 웹사이트는 일부만 바뀌는경우가 많아서 그러면 정보이득이 낮고 HTML은 양이 많아서 시퀀스가 너무 길어진다는 치명적인 문제가 있음.

그래서 저자들은 Model based RL에서 너무 큰 원시 입력을 latent space로 보내는것에서 영감을 받아서 원시 상태가 어떻게 변화했는지 추상화하는 방식을 개발함.

![논문 Figure 5: transition-focused observation abstraction 개요 - 헝가리안 알고리즘으로 요소를 매칭해 상태 변화를 추출하고 LLM이 자연어로 요약](/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig5.png)

개인적으로 이 과정이 히트였다고 생각함.
단순히 $$o_t,o_{t+1}$$을 주고 LLM에 변화를 요약하라고 하면 할루시네이션이나 빼먹는 정보가 생길 수 있으므로 먼저 헝가리안 알고리즘을 사용함.

헝가리안 알고리즘은 비용행렬을 보고 최적의 쌍을 매칭해주는 알고리즘이라고 함([https://billionaire-hossa.tistory.com/36](https://billionaire-hossa.tistory.com/36)).
비용행렬을 나이브하게 비슷한 위치에 있는 애로 만들면 웹페이지가 바뀌었을때 누가 누군지 잘 못찾고 다 틀리고 난리가 날텐데, 여기서는 태그 종류, 텍스트 내용이나 속성등의 다양한 요소를 종합적으로 고려해 짜는것같음.
이렇게 하면 웹페이지 요소들이 변하거나 해도 비교적 Robust하게 같은 요소들을 추적할 수 있음.
어쨌든 저런 표현력이 좋은 비용행렬로 요소들을 추적한다음, 기계적으로 요소들의 차이를 추출하고, 그걸 LLM에 입력해서 자연스러운 요약 $$\tilde{o}_{t+1}$$로 변환함.

그 과정까지 거치면 world model 훈련을 위한 데이터셋 $$\tilde{\mathcal{D}}=\sum_{t=1}^n\{I,o_t,a_t,\tilde{o}_{t+1}\}$$가 완성됨!

**4.1.3 Step3: Learning environment dynamics**

그렇게 완성된 모델 $$\tilde{D}$$로 $$\mathcal{L}_\phi=-\log \sum_{(\tilde{o},o,a,I)}p(\tilde{o}_{t+1} \mid o_t,a_t,I)$$ 이렇게 환경모델 훈련.

### 4.2 Inference time policy optimization with the world model

WMA는 정책모델 $$\theta$$, 월드모델 $$\phi$$, 가치함수 $$V$$로 구성됨.
추론시에는 $$\text{top-p}$$ 디코딩을 이용해 $$\{a_t^1,a_t^2,...,a_t^k\} \sim \pi_\theta(\cdot \mid o_t)$$ 여러개의 행동 후보들을 샘플링하고, 환경모델을 돌려서 세트로 $$\{\tilde{o}^1_{t+1},\tilde{o}^2_{t+1},...,\tilde{o}^k_{t+1}\}$$ 추상화된 다음 관측을 샘플링함.

이후 가치함수로 $$\hat{a}_t=\argmax_{a_t\in \{a_t^1,a_t^2,...,a_t^k\}} V(I,o_t,a_t^i,\tilde{o}^i_{t+1})$$ greedy하게 최적의 행동을 선택함.
가치함수는 $$V(I,o_t,a_t^i,\tilde{o}^i_{t+1})$$  이렇게 일반적인 상태가치함수랑 다르게 생겼고, 이것도 모델이라고 함.
이렇게 world model을 이용해서 추론하면 보통 GPT같은 closed 모델을 사용하는 정책모델을 학습하지 않고도 웹 에이전트의 선택을 최적화 할 수 있음.

---

## 5. Experiments

### 5.1 Setups and implementation details

**월드모델**
월드모델로는 Llama-3.1-8B instruct를 사용함.
월드모델 $$p_\phi(\tilde{o}_{t+1}\mid o_t,a_t,I)$$는 task에 따라 달라지므로 벤치마크의 trajectory를 수집해서 벤치마크에 맞게 fine-tuning해줌.
Mind2Web은 trajectory 데이터가 있어서 바로 사용할 수 있지만, WebArena는 trajectory 데이터 없이 그냥 시뮬레이션 환경만 띡 주는거라 instruction $$I$$와 trajectory도 합성해서 만들어 씀.

**정책모델**
정책모델로는 GPT-4o를 사용함.

**가치함수모델**
월드모델과 동일하게 Llama-3.1-8B instruct를 사용하는데, 이건 월드모델과 달리 벤치마크마다 fine-tuning하지 않고 그냥 Mind2Web 데이터로 fine-tuning해서 다 쓰는것같음.
근데 전통적인 RL의 가치함수가 아님.
생긴것도 $$V(I,o_t,a_t^i,\tilde{o}^i_{t+1})$$ 이렇게 상태가치함수 $$V(s)$$랑 다르게 생겼고, 훈련방식이 완전 가짜임.
원래 RL에서는 TD를 하던 MC를 하던 $$v_\pi(s)=\mathbb{E}_{\pi }[G_t \mid S_t=s]$$ 이렇게 수익(누적보상)의 기대값을 상태가치함수로 쓰는데, WMA의 가치함수는 보상이랑 닿아있지 않고 수익을 바로 라벨링해서 지도학습 함.
$$t/len(\tau)$$ 이런식으로 가치함수의 라벨을 정의해서, 10단계의 task에서 8단계를 잘 하면 0.8점 이런식임.

베이스라인으로는 사용한 애들중에 완전 처음본 애들은
BrowserGym : HTML 콘텐츠와 브라우저 화면을 같이 멀티모달로 학습
SteP : 인간이 수작업으로 작성한 계층적 정책 사용
HTML-T5 : HTML 코퍼스로 pre-train 된 기존의 SOTA

### 5.2 Main results

![논문 Table 1: WebArena에서 에이전트별 성공률과 행동 선택(policy optimization)에 따른 상대적 향상](/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig6.png)

이렇게 만든 WMA라는 방법론이 그래서 실제로 쓸모가 있는지 실험을 진행함.
실험 세팅이 어떤건 GPT-4를 쓰고 어떤건 GPT-4o를 쓰고 하는데, 기존 baseline들은 실험을 직접 안돌리고 논문에 나온 데이터를 그대로 쓰기 위해서 그런거같다고 함.
또, max actions도 어떤건 30 어떤건 5고 max actions가 뭐 한 에피소드당 허락된 행동의 수인지 아니면 행동 후보 k를 말하는건지도 불분명하고 그런데, 아마 에피소드당 최대 행동수인것같음…
고차원의 long horizon task에서 5step만에 뭘 하라는게 말이 되는건가 싶지만 아마 연산량 실험을 위해 설정한것같다고 함.
이런 애매한 실험세팅도 그렇고 GPT-4의 베이스라인들이 점수가 높게 나오는것도 그렇고 뭘 하고싶은 실험들인지 잘 모르겠지만, 그냥 CoT보다는 확실히 좋다는점을 어필하고싶은듯 함.
결과를 보면 Tree search agent보다는 점수가 낮지만 CoT보다는 유의미하게 점수가 높은걸 확인할 수 있음.
Tree seach agent는 여러 경로중 하나를 선택하는게 아니라 각 경로를 실제로 실행해보는 방식이라고 함.
이 점을 고려한다면 WMA의 결과도 충분히 훌륭한듯.

![논문 Table 2: GPT-4o-mini를 정책 모델로 쓴 에이전트의 도메인별 성능 (Vanilla CoT 대 WMA)](/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig7.png)

GPT-4o-mini에서  제대로 CoT랑 WMA를 비교하는데, 편차는 있지만 모든 도메인에서 CoT를 상회한것을 확인할 수 있음.

![논문 Table 3: GPT-3.5-Turbo를 정책 모델로 쓴 Mind2Web 테스트의 Cross-Task, Cross-Website, Cross-Domain 성공률](/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig8.png)

Mind2Web에서도 WMA를 실험해봤음.
Cross-Task, Cross-Website, Cross-Domain은 점점 높은수준의 일반화능력이 필요한 세팅이라 사실상의 난이도역할을 한다고 함.
가령 Cross-Task는 훈련에서 쿠팡에서 휴지를 사는걸 배웠다면 평가때는 슬리퍼를 사라고 하는식이고, Cross-Website는 평가때 G마켓에서 뭐 사오라고 하는식, Cross-Domain은 정부 민원사이트 들어가서 뭐 시키는 식.

여기서는 가장 강력한 라이벌인 Tree seach agent를 못씀.
Mind2Web이 살아있는 시뮬레이터가 아니라 teacher forcing하면서 진짜 사람의 trajectory를 매 스텝 맞추게하는 벤치마크라 경로를 실제로 실행해볼수가 없기때문이라고 함.
모로가도 서울만 가면 장땡인데 사람의 trajectory만 정답으로 인정하는 억까가 존재하는 벤치마크같음…

Step SR, EA, AF1은 에피소드의 스텝마다 계산되는값이라, 아마 평균을 적어놓은것같음.
그리고 재밌게도 AWM의 element filtering이 오히려 성능을 저해한다는 족쇄를 발견해서 저자들이 저걸 풀어준 w/o EF 버전으로도 실험을 진행했음.
결과를 보면 확실히 WMA를 사용했을때 성능이 유의미하게 오른듯.

### 5.3 Analyses of time and cost efficiency

![논문 Table 4: Tree search agent와 WMA의 성공률, API 비용, 추론 시간 직접 비교](/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig9.png)

여기가 숙적 Tree search agent한테 카운터펀치를 먹이는 가장 중요한부분같음.
앞선 실험결과들을 봤을때는 WMA이 좋다고 해도 Tree search agent한테는 성능이 딸리네 생각했는데, Tree search는 실제로 경로들을 실행하기때문에 상당히 계산비용과 시간이 많이 들어감.
특히 원래상태로 돌아갈때는 진짜 다시 백트래킹까지 함.

표를 보면 시간은 5배, API비용은 7배가 싸서, world model로 시뮬레이션만 수행하는 WMA의 우월함을 확 느낄 수 있음.
그리고 Shopping을 제외한 도메인에서는 성능도 거의 차이도 안남.
저자들은 Shopping이 복잡해서 world model이 예측을 어려워하기때문인것같다고 추측함.

### 5.4 Ablation studies

![논문 Table 5: WebArena에서의 ablation 결과 (보상 추정에 다음 상태 미사용, world model 미학습, 관측 추상화 미사용)](/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig10.png)

Ablation을 통해 (유사)가치함수에 다음 관측 $$o_{t+1}$$을 넣으면 성능이 좋아지는게 맞는지 실험.
결과적으로 다음 관측 넣은게 성능 더 좋았음.

world model을 만들때도 fine-tuning으로 월드모델 $$p_\phi(\tilde{o}_{t+1}\mid o_t,a_t,I)$$을 만드는 자기들 방식이랑 그냥 2-shot 주고 GPT-4o-mini한테 예측해보라고 한 방식 비교했을때도 fine-tuning이 더 좋았고.

또, 다음 관측을 원시 관측 $$o_{t+1}$$ 대신 $$\tilde{o}_{t+1}$$ 쓰는게 좋은게 맞는지 확인해봤는데 원시관측 쓰면 성능이 떡락했음.

<div style="display:flex; gap:12px; align-items:center;">
  <figure style="width:56%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig11.png" alt="논문 Table 6: 가치함수 모델 종류에 따른 성능 (GPT-4o-mini 대 fine-tuning한 Llama-3.1-8B)" style="width:100%;">
  </figure>
  <figure style="width:42%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig12.png" alt="논문 Figure 6: 샘플링한 행동 수 k에 따른 성공률 ablation" style="width:100%;">
  </figure>
</div>

가치함수와 k-action scaling실험도 진행했음.
먼저 가치함수를 Llama를 fine-tuning하는게 아니라 GPT한테 평가하는방식을 사용했는데, fine-tuning이 조금 더 좋았다고 함.
근데 Mind2Web으로 fine-tuning 한 가치함수모델을 WebArena에서도 쓰니까 절반정도만 task specific이긴 하지만 그래도 고작 저정도 점수차이면 완전 task agnostic하고 일반적인 GPT쓰는게 더 좋을것같음.

$$\{a_t^1,a_t^2,...,a_t^k\} \sim \pi_\theta(\cdot \mid o_t)$$으로 샘플링하는 action들을 scaling하면 성능이 확실히 오른다는것도 확인.

---

## 6. Further analyses

### 6.1 Combining self-refine with our world models

<figure style="width:48%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig13.png" alt="논문 Table 7: 시뮬레이션된 환경 피드백으로 GPT-4o-mini에 self-refine을 적용한 결과" style="width:100%;">
</figure>

world model을 이용해서 self-refine하는 방식도 테스트해봄.
근데 이렇게 $$\{a_t^1,a_t^2,...,a_t^k\} \sim \pi_\theta(\cdot \mid o_t)$$ 행동 여러개 샘플링하는건 아니고, $$a_t$$ 하나만 샘플링해서 self-refine을 통해 행동을 수정하는 방식임.
Vanilla CoT에 비해서는 성능이 조금 올랐지만, WMA처럼 여러개 뽑는방식에 비하면 한참 부족.

### 6.2 Types of errors in world model’s predictions

world model을 자세히 보기 위해 정성적인 평가를 진행함.
예측 $$\tilde{o}_{t+1}$$이 오류인지는 컴퓨터공학 전공자가 주관적으로 판단했음 ㅋㅋㅋㅋ

<figure style="width:61%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Web-Agent-with-World-Models/web-agent-with-world-models-fig14.png" alt="논문 Figure 7: world model이 예측한 잘못된 관측의 오류 유형 통계 (Low function competence 26%, Counterfactual imagination 42% 등)" style="width:100%;">
</figure>

결과가 재밌었는데, 맞는말이지만 하나마나한 자명한 예측을 경우, 웹 기능에 대한 이해도가 떨어져서 틀린 예측을 하는경우, 존재하지 않는 뭔가를 예측하는 할루시네이션등이 있었고, 할루시네이션이 42%로 비중이 높았음.

---

## 7. Conclusions

LLM 웹 에이전트에 최초로 world model을 도입한 연구고, 효과적인 환경 시뮬레이션 방식으로 다른 베이스라인 에이전트들을 능가했다고 하면서 마무리.

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>🦅</div>
<div markdown="1" style="flex:1; min-width:0;">

**전체적인 방법론**<br>
추론: HTML을 간단히 나타낸 접근성 트리 $$o$$가 있으면 $$\pi(a\mid o)$$로 여러 행동들 샘플링하고, 환경모델로 예상되는 관측변화에 대한 자연어요약을 $$\tilde{o}$$로 예측.<br>
이후 (유사)가치함수로 각 행동 후보들의 가치를 계산한 후 가장 좋은 행동 선택.<br>
World model 훈련: 종합적으로 웹 요소 비용행렬 계산 후 헝가리안 알고리즘으로 매칭.<br>
이후 바뀐점을 1차적으로 기계적으로 표현, 2차적으로 LLM에 자연어로 요약하게 만들어서 $$\tilde{o}$$ 제작.<br>
그리고 그 데이터로 World model $$p(\tilde{o}\mid o,a,I)$$ 훈련.

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>😲</div>
<div markdown="1" style="flex:1; min-width:0;">

**느낀점**<br>
되게 좋은 논문이라고 생각했는데, world model을 LLM 에이전트에 도입한다는 이 중요한 아이디어를 왜 다른사람들은 안냈을지 의아했음.<br>
관측을 자연어로 추상화해서 효율과 일반성을 다 잡은점, 그리고 환경모델 훈련시킬 데이터 $$\tilde{o}$$ 만들때 바로 변화를 요약하라고 하는게 아니라 헝가리안 알고리즘과 기계적 방법등을 조합해 할루시네이션이나 빼먹는 정보 없이 요약하게 한게 상당히 참신했음.

</div>
</div>
