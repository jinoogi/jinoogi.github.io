---
title: Inference-time Scaling 리뷰
date: 2026-09-20 00:32:00 +0900
categories: [AI Paper Reviews, Reasoning & RL]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters**<br>
Date : 2024.8.6<br>
Venue : arXiv<br>
Comprehension : 2.5

</div>
</div>

## 0. Abstract

2020년의 scaling law 논문을 시작으로, 학계에서는 모델 학습단계의 스케일링 법칙 등은 잘 연구했는데, 추론단계에서의 스케일링 법칙은 별로 다루지 않았다고 함.
그래서 저자들은 Verifier를 활용한 정답탐색과 적응적 업데이트라는 두가지 모드로 추론단계를 시도해봤는데, 문제 난이도에 따라 적합한 모드가 달라졌다고 함.
그래서 이런 결과들을 바탕으로, 효율적인 연산 최적화 전략을 제시함.

---

## 1. Introduction

사람도 어려운 문제를 만났을때 오래 생각하면서 생각을 개선하는데, LLM에도 적용할수 없을까? 하는 생각에서부터 출발했다고 함.
그래서 기존의 연구들을 봤는데, 어떤 연구들은 추론시간 스케일링을 하면 성능이 오른다고 하고, 또 어떤 연구들은 안 오른다고 하고 주장이 뒤죽박죽이었다고 함. 그래서 자기들이 제대로 체계적으로 연구할 필요성을 느낌

스케일링도 스케일링 할게요! 한다고 바로 되는건 아니고, 어떻게 할지 정해야되는데, 기존의 연구들은 추론시간 스케일링에 N개의 출력을 병렬로 생성하고 제일 좋은걸 쓰는 best-of-N으로 스케일링하는 방식을 주로 썼다고 함. 
여기서는 적응형 업데이트방법이나 Verifier를 이용한 탐색법을 위주로 사용하고 연구해봄.
적응형 업데이트방법은 스스로의 답변을 고쳐나가는 reflection 같은거고, Verifier는 PRM을 통해 단계별로 좋은답변을 선택하는 경로를 고르는 방법임. 

이 연구는 특별히 fine-tuning된 PaLM-2 모델을 이용해서 MATH 벤치마크에서 수행되었고, 앞서 말한 2가지의 접근법을 실험해봄.
쉬운문제들에서는 답변을 수정하는 적응형 업데이트방법이 더 좋았고, 어려운 문제들에서는 PRM으로 최적의 정답을 tree-search하는 방법이 더 좋았다고 함.
이 결과를 기반으로, 수정과 탐색을 조정해서 사용하는 적응적 추론전략을 만들었더니 컴퓨팅은 4배 덜 들어가면서도 성능은 best-of-N 방법을 따버렸다고 함.

또, pre-train단계에서 컴퓨팅을 쏟아붓는 기존의 scaling 과도 비교해봤는데, 쉬운문제부터 특정 어려운문제까지도 자기보다 14배 큰 사전모델보다 추론시간을 스케일링하는 모델이 더 나았다고 함.
다만 아주 어려운문제에서는 추론시간 스케일은 별로였고 훈련 스케일링으로 모델크기를 키우는게 나았다고 함.

---

## 2. A Unified Perspective on Test-Time Computation: Proposer and Verifier

LLM의 응답을 업그레이드하는 방법에는 2가지가 있다고 함.

1. 입력수준에서 추가 토큰들을 덧붙여 LLM이 나은 답을 출력하도록 하는방법 (제안자)
2. LLM에서 여러 응답을 샘플링하고 이것들을 가지고 뭔가를 하는방법 (검증자)

모델 자체가 더 나은 응답을 출력하도록 하는 제안자 방법에는 STaR같은 강화학습 기반 방법론과 Self-Critique같은 SFT 방법론이 있는데, 둘다 자기가 푼 on-policy 데이터로 학습하지만 STaR는 맞힌 문제만 계속 RL로 학습시켜서 완벽주의자를 만들어내는 느낌이라면, Self-Critique는 오답을 같이 넣고 SFT를 돌려서 틀렸을때 회복탄력성을 늘려주는 방법이라고 함.
그리고 자기들은 여기서 Self-Critique 방법론을 사용한다고 함.

검증자측면의 방법에는 보통 best-of-N 을 쓰는게 정석이었지만, 자기들은 여기서 단계별 평가를 하는 PRM을 도입하고, 그렇게 함으로서 정답공간에 대한 Tree-search를 수행할 수 있게 된다고 함.

---

## 3. How to Scale Test-Time Computation Optimally

### **3.1. Test-Time Compute-Optimal Scaling Strategy**

해결하고자 하는 목표를 말이 아니라 수식으로 표현하면

$$
\theta^{*}_{q,a^*(q)}(N)=\argmax_\theta(\mathbb{E}_{y \sim Target(\theta,N,q)}[\mathbf{1}_{y=y^*(q)}])
$$

이런식으로 프롬프트 $$q$$와 컴퓨팅 $$N$$이 주어졌을때 답변의 정확도를 최대화하는 하이퍼파라미터 $$\theta$$를 구하는 문제로 정의함.

### 3.2. Estimating Question Difficulty for Compute-Optimal Scaling

근데 최적 추론스케일링 방법을 고르려면, 먼저 문제의 난이도부터 알 수 있어야함.
난이도 평가에는 2가지 방법이 있는데, Oracle difficulty와 Model predicted difficulty임.

먼저 하나개의 질문에 대해 모델을 돌려서 2048개의 답변을 생성하는데, 이 답변을 ground truth와 비교해서 정답률을 가지고 5분위수로 구분하면 Oracle difficulty이고, 답변을 Verifier가지고 평가하면 Model predicted difficulty임.

실제로 문제 풀때는 답을 모르니까 Oracle difficulty 는 못쓰고 Model predicted difficulty를 써야하는데, 여기에 컴퓨팅이 많이 필요하다는 trade-off가 있을거라고 함.

---

## 4. Experimental Setup

데이터셋으로는 MATH를, 모델로는 PaLM 2-S 모델을 사용했다고 함.
우선 MATH 선택이유로는, 아예 못푸는게 아니라 풀수있는 역량은 있는데 잘 추론하는게 어려운 상황에서 추론시간 스케일링이 잘 먹힐것으로 예상해서 그렇다고 함.
모델로는, PaLM 2-S가 아직 덜 포화돼서 추론시간 스케일링의 위력을 보여줄수 있는 여지가 남아서 그렇다고 함.

---

## 5. Scaling Test-Time Compute via Verifiers

이 장에서는 Verifier를 이용해서 추론시간 스케일링 하는 방법을 주로 다룸

### 5.1. Training Verifiers Amenable to Search

Verifier를 이용해 만들어진 답변들에서 좋은 답변을 선택하는 과정을 설명.
PRM을 만들때 원래는 PRM800k라는 GPT-4가 만든 답변에 중간과정을 인간이 채점하고 라벨링해놓은 데이터를 SFT 하는방식을 썼다고 함.
근데 그게 distribution이 달라서인지, 이 PaLM2에는 잘 안먹혀서 다른방식으로 수정함.
강화학습에서 자주 본 reward-to-go 의 추정치를 구하는방식으로 전략을 수정했고, 각 단계에서 몬테카를로 샘플링을 통해 각 단계의 가치를 추정함.

이제 그렇게 만들어진 PRM으로 답을 선정할때는, Step-wise aggregation → Inter-answer aggregation 순서로 진행함.
먼저 step-wise는 각 답변의 점수를 매기는 방법인데, 기존에는 단계별 점수를 곱하거나 최소값을 취하는 방법도 많이 썼지만 마지막단계의 점수를 선택하는 방식으로 한 답변의 점수를 평가하는게 제일 좋았다고 함.

그 다음은 답변간 점수를 비교하는 Inter-answer인데, 답이 같은 애들끼리 그룹을 지어서 점수를 합산한다음 총합이 가장 큰 그룹의 답을 선택하는 best-of-N weighted 방식을 사용한다고 함.

### 5.2. Search Methods Against a PRM

Verifier를 이용해 좋은 답변들을 만들어내는과정을 설명함.

![논문 Figure 2: PRM 탐색 방법 비교 - Best-of-N, Beam Search, Lookahead Search](/assets/img/ai_paper_reviews/Inference-time-Scaling/inference-time-scaling-fig1.png)

best-of-N weighted는 아까 설명했던 방법이고, 그냥 여러개 생성해서 좋은거 고르는 방식의 일종임.

Beam-search는 단계별로 N개의 후보만 남기는방식으로 탐색하는 방식

Lookahead search는 단계별로 선별할때 현재 단계가 아니라 미래 단계까지 반영한 방식.
PRM이 이론적으로 완전한 가치함수라면 아무 쓸데없는짓이지만 그렇지 않기때문에 유효하다고 함

### 5.3. Analysis Results: Test-Time Scaling for Search with Verifiers

![논문 Figure 3: generation budget에 따른 PRM 탐색 방법별 MATH 정확도(왼쪽)와 난이도별 Beam Search·Best-of-N 비교(오른쪽)](/assets/img/ai_paper_reviews/Inference-time-Scaling/inference-time-scaling-fig2.png)

방금 본 Verifier를 이용한 답변생성(탐색) 알고리즘들을 실험을 통해 비교함.
컴퓨팅과 난이도 두 측면에서 주요 비교가 이루어짐.

예산이 적을때는 beam-search가 훨씬 좋다가, 컴퓨팅이 많아지니까 best-of-N weighted가 성능이 더 좋아졌다고 함.

![논문 Figure 29: PRM beam search 예시 - 정답을 낸 뒤에도 의미 없는 문장을 반복하며 높은 점수를 받는 출력](/assets/img/ai_paper_reviews/Inference-time-Scaling/inference-time-scaling-fig3.png)

Look ahead는 성능이 별로 안좋았는데, 과도하게 PRM신호를 활용했더니 이런식으로 아무 영양가없는말을 반복하는 경향도 보이고 그랬다고 함.
즉, 불완전한 PRM에 과도하게 최적화되어 안좋은점도 너무 잘 반영하게 된 느낌인듯

다음으로는 문제 난이도별로 탐색알고리즘들을 분석해봄.
level 1,2의 쉬운 문제에서는 컴퓨팅이 증가할수록 beam search가 PRM을 과도하게 활용하면서 성능이 떨어짐.
level 3,4의 좀더 어려운 질문들에서는 beam search가 best-of-N보다 항상 좋았다고 함.

정리해보자면, 컴퓨팅이 늘어나는건 best-of-N한테는 시험 응시기회가 늘어나는느낌이라 성적이 올라감.
beam-search 한테는 훈수(PRM)받을수 있는 기회가 늘어나는 느낌인데, 훈수도 적당히 받아야지 사칙연산할때처럼 모든단계에서 훈수받으면 오히려 방해된다고 함.
난이도측면에서 보면, 쉬운건 훈수에 집중할필요없이 자기 쪼대로 하는게 좋고, 어려운건 훈수를 좀 잘 들어가면서 푸는게 좋다는 이야기인거임.

<figure style="width:75%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Inference-time-Scaling/inference-time-scaling-fig4.png" alt="논문 Figure 4: 난이도에 따라 test-time compute를 배분한 compute-optimal 탐색과 PRM Best-of-N 등 baseline 비교" style="width:100%;">
</figure>

그래서, 결론적으로는 Verifier를 이용한 최적답변탐색방법이 컴퓨팅 예산과 질문의 난이도에 의존한다는걸 알아냈고, 이를 적응형으로 섞어쓰는 방법을 도입하면 이런식으로 훨씬 적은 컴퓨팅만으로도 best-of-N을 능가할수 있다고 함.

---

## 6. Refining the Proposal Distribution

5장에서 Verifier로 스케일링했다면, 이 장에서는 이제 자신의 답안을 수정해가면서 답변 자체를 바꾸는 방식의 추론시간 스케일링 방식을 연구함.
Qu et al. 의 논문 Recursive Introspection의 방법론을 베이스로하는데, 이 논문은 [질문]→[정답] 이렇게 싱글턴 추론만 학습하던 기존 AI와 다르게 [질문]→[오답1]→[오답2]→…→[정답] 이렇게 앞에있는 답들이 틀렸을때 그걸 문맥정보로 사용해서 더 나은 답을 도출하는 멀티턴 과정을 학습시키는 방법임.

### 6.1. Setup: Training and Using Revision Models

근데 저 Recursive Introspection은 계산비용이 많이들어서 자기들 인프라로는 할수가 없었고, 대신 가짜로 on-policy 데이터처럼 보이는 trajectory를 구성하는 방식을 개발함.
우선 temperature을 높여서 한 질문에 대해 64개의 다양한 응답을 샘플링하고, 그걸 그럴듯하게 배치해서 틀렸다가 정답으로 가는 과정을 모사하게 함.
그럴듯하게 시계열적으로 상관관계를 갖도록 구성하지 못하면, 이전 문맥을 무시하고 그냥 처음부터 다시 풀어버릴려고 하기때문에 이걸 잘 하는게 매우 중요한데, 문자단위 편집거리라는 지표를 이용해 상관성을 측정하고 trajectory를 구성한다고 함.
다만, 특이하게도 모든 스텝의 trajectory를 그렇게 구성하는게 아니라, 마지막 스텝만 그렇게 구성하고 나머지는 그냥 랜덤으로 섞어놓는다고 함.

![논문 Figure 6: revision 단계별 pass@1(왼쪽)과 sequential 대 parallel 샘플링 비교(오른쪽)](/assets/img/ai_paper_reviews/Inference-time-Scaling/inference-time-scaling-fig5.png)

위의 왼쪽 그래프처럼 trajectory의 revision chain을 길게 해줄수록 성능이 올라갔는데, 치명적인 단점이 있었다고 함.
훈련때는 주어진문맥이 항상 오답이었지만, 테스트때는 맞는답변이 revision 대상으로 문맥에 들어갈수 있음.
그렇게되면 맞는답도 고쳐버릴려고해서, 순차적 majority voting 또는 verifier를 이용해서 시퀸스 $$A_1 \rightarrow A_2 \rightarrow A_3 ...$$ 중에서 가장 좋은 답을 고르게 했다고 함.

그리고, 6장에서 도입한 Sequential 방법과, 5장에서의 Parallel 방법을 비교해봤는데, 오른쪽 사진처럼 Sequential 방법(best-of-N weighted)가 더 좋았었다고 함.

### 6.2. Analysis Results: Test-Time Scaling with Revisions

근데 Parallel보다 revision을 하는 Sequential이 성능이 더 좋긴했지만, 사실 직관적으로는 그것보단 서로 성질이 다를거라고 예상할 수 잇음.
Parallel은 전역적으로 조사하는 탐험, Sequential은 탐사로 고려할 수 있고, 이걸 섞어서 쓰면 성능이 오르는 골디락스존을 찾을수 있을거라고 추측가능.

![논문 Figure 7: sequential/parallel 비율에 따른 MATH 정확도(왼쪽)와 난이도별 최적 비율(오른쪽)](/assets/img/ai_paper_reviews/Inference-time-Scaling/inference-time-scaling-fig6.png)

그래서 실험을 해보니 이렇게 컴퓨팅 예산과 문제 난이도별로 최적의 Sequential:Parallel 비율이 달라졌다고 함.

---

## 7. Putting it Together: Exchanging Pretraining and Test-Time Compute

![논문 Figure 9: FLOPs를 맞춘 조건에서 pretraining compute와 test-time compute의 tradeoff (Revisions, PRM Search)](/assets/img/ai_paper_reviews/Inference-time-Scaling/inference-time-scaling-fig7.png)

여기서는 그래서 제한된 컴퓨팅자원이 있을때, 어떤식으로 써먹는게 효율적일지 테스트함.
작은모델로 추론시간 스케일링을 한 경우과, 14배 큰 모델을 훈련시키고 추론시간 스케일링은 없는경우를 비교했는데 위의 그래프에서 별로 표시한게 경계선임.
별보다 더 좋으면 추론시간 스케일링을 하는게 좋은경우라고 함.
추론이 많을수록, 난이도가 어려울수록 추론시간스케일링보다 큰 모델을 쓰는게 유리한것을 알 수 있음

---

## 8. Discussion and Future Work

추론시간 스케일링을 위해 verifier 기반 탐색이나 revision을 이용하는 방법을 연구했고, 문제의 난이도와 컴퓨팅에 따라 최적의 추론시간 스케일링 전략이 달라진것을 확인했음.
이를 응용한 연산 최적화전략을 제시했고, 경우에 따라서 추론시간 스케일링을 사용하지 않는 14배 큰 모델보다도 높은 성능을 보일 수 있음을 보임.
마지막으로는 추후 이어서 연구해볼수 있는 내용들을 제시하고 마무리.

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>😲</div>
<div markdown="1" style="flex:1; min-width:0;">

**느낀점**<br>
사실 스케일링법칙 논문도 그렇고 이 추론시간 스케일링법칙도 그렇고 짜임새있게 이해되면서 체화시킬수있는 논문이라기보다 실험결과들을 난잡하게 던져놓고 해보니까 이런식으로 되더라 같은 논문이라 읽을맛이 잘 안나는 논문같음…<br>
그래도 verifier 기반 탐색과 revision 방법등을 이용해 추론시간 스케일링을 할 수 있다는 사실은 알겠고, 14배 큰 모델이랑도 비벼볼수 있다는 사실은 흥미로웠음

</div>
</div>
