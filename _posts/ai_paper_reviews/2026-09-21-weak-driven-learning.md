---
title: Weak driven learning 리뷰
date: 2026-09-21 00:54:00 +0900
categories: [AI Paper Reviews, 기타]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Weak-Driven Learning: How Weak Agents make Strong Agents Stronger**<br>
Date: 2026.2.9<br>
Venue: arXiv<br>
Notable author: -<br>
Comprehension: 2.5단계

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>😲</div>
<div markdown="1" style="flex:1; min-width:0;">

**느낀점**<br>
음... 근데 아무리 생각해도 일괄적으로 1스텝 전의 weak 모델과 비교하는건 그리 좋은 방법은 아닌것같아<br>
문제별로 4스텝 전의 weak모델에서 배울점이 많은게 있을거고, 1스텝전의 weak모델에서 배울점이 많은게 있을거고 그럴건데...<br>
그리고 커리큘럼 선별할때 정답라벨에 대한 크로스엔트로피 손실이 더 나을것같음.<br>
엄밀히말하면 이 모델이 배울게 있다고 판단하는 문제는 내가 예전에 못푼문제라기 보다는 빠르게 학습된 문제라고 보는듯

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>🦅</div>
<div markdown="1" style="flex:1; min-width:0;">

**들어가기전 큰그림**<br>
신경망을 학습할때 결국 loss는 정답분포를 가지고 계산하기때문에 정답분포를 완벽히 맞춰버리면 더 이상 학습압력이 발생하지 않음<br>
근데 이게 그냥 문제집이 포화돼서 학습신호가 안 나오는거고, 결정경계를 더 세밀하게 다듬을 여지가 있는데 안주하는것일수도 있음.<br>
물론 강한 신경망이 잘 못푸는 더 어려운 문제집을 가지고오면 학습신호가 살아나겠지만 그건 너무 비싸기때문에, 과거의 약했던 신경망의 경험을 섞어서 학습신호가 나오게 데이터를 다시 쥐어짜는거임.<br>
사람으로 치면 수학문제풀때 어설프게 정답만 맞춘 문제는 복습하면서 잘 몰랐던 부분을 공부하고 풀이를 매끄럽게 만드는것처럼…

</div>
</div>

## 0. Abstract

LLM을 훈련할때, 모델이 이미 확신을 갖게되면 더 학습해도 성능이 안 오르는 plateau가 발생하므로, 과거 약한 상태였을때의 체크포인트를 써서 과거에 어려워했던점을 학습하게 함으로서 학습이 포화된 지점을 극복하겠다고 함.

---

## 1. Introduction

![논문 Figure 1: 패러다임 비교 - Teacher의 logits를 모방하는 Distillation-Based Learning과, 약한 모델의 corrective signal로 강한 모델을 더 강하게 만드는 Weak-Driven Learning (평균 정확도 Weak 47.4, Strong 61.0, Weak-Driven 69.1)](/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig1.png)

SFT나 Knowledge distilllation 같은걸 보면 결국 공통적으로 로짓같은 target을 모방하는 방식임.
그래서 나중에 target과 가까워지고 포화되면 학습신호가 약해지는 문제가 있음.
저 문제를 해결하기위해 self-revision이나 reflection같은 방법들을 만들었는데, 그것들조차도 결국 자만에 빠진 우등생한테 다시 풀어보게 하는식이라 건성으로 슥슥 보고 넘기는식으로 한계가 명확했다고 함.
자기들은 우등생한테 과거 오답노트 풀이에서 어설프게 넘어간부분을 딱 들고와서 “헉” 하게 만드는 방법.

이런 종류의 학습방법을 Weak-driven learning이라고 정의했고, 구체적으로는 강한모델 $$M_{strong}$$과 약한모델 $$M_{weak}$$의 로짓 불일치를 이용해 강한 모델을 더 강한모델 $$M_{strong}^+$$로 만드는 방법으로 정의함.

---

## 2. Related work

SFT나 KD계열은 결국 모방기반 목적함수를 사용하는 strong-to-weak 구조이고, 자기들은 weak-to-strong 계열의 방법이라는것.

---

## 3. Preliminaries

![손그림: 로짓 z가 softmax를 거쳐 출력 확률이 되는 분류기 구조와 cross entropy loss, 정답 로짓과 오답 로짓에 대한 그라디언트 식](/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig2.png)

분류문제에서 토큰단위 cross-entropy loss는 $$L=-\log P_\theta(y\mid x)$$ 이고,
그라디언트는 $$\frac{\partial L}{\partial z_t[k]}=P_\theta(k\mid x)-\mathbb{I}[k=y]$$ 가 된다는 당연한 내용 recap

---

## 4. How can weak make strong stronger

![논문 Figure 2: WMSS 개요 - Stage 1 약한·강한 에이전트 초기화, Stage 2 엔트로피 기반 커리큘럼으로 active data 선별, Stage 3 로짓 혼합을 통한 joint training](/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig3.png)

전체적인 방법론을 보면, stage2에서는 학습하는것이 아니고 학습을 위한 커리큘럼을 생성하는 단계임.
그리고 요즘 파이프라인처럼 base model→SFT→RL 순서가 아니라 base model→변형된 SFT만 하는 구조.

<figure style="width:64%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig4.png" alt="논문 Algorithm 1: Weak Agents make Strong Agents Stronger 의사코드 - 초기화 후 커리큘럼 데이터 선별과 로짓 혼합 학습을 K번 반복" style="width:100%;">
</figure>

**Stage1: initialization** 

먼저, base model $$M_0$$을 $$M_{weak}$$로 초기화하고, base model을 SFT한  $$M_1$$을 $$M_{strong}$$으로 초기화함.

**Stage2: Design curriculum**

$$
p_i\propto \alpha H(\mathcal{M}_{\text{weak}};x_i)+\beta[-\Delta H_i]_++\gamma[\Delta H_i]_+
$$

이런식으로 커리큘럼 데이터셋으로 뽑을 확률을 설정함.
여기서 커리큘럼은 흔히 아는 쉬운것부터 어려운 순으로 배치하는 방법론을 말하는게 아니라, 전체 데이터 중 이번에 학습할 데이터셋을 골라내는거라 함.

첫번째 term은 절대적인 난이도 자체가 높았던 문제를 골라내는 base difficulty term임.

두번째 term은 consolidation term으로, 확신이 빠르게 올라간 문제를 골라내는 역할을 함.
빠르게 배운 문제는 자만했을 가능성이 높다고 보는 방식으로, 이 방법만의 고유하면서도 가장 중요한 term인듯.

세번째 term은 학습에 뭔가 문제가 있어서 오히려 확신이 내려간 경우를 catastrophic forgetting으로 보고 복구하는 regression repair term.

보면 consolidation, repair term은 $$\Delta H_i=H(\mathcal{M}_{\text{strong}};x_i)-H(\mathcal{M}_{\text{weak}};x_i)$$ 이런 엔트로피 변화를 이용함.
”아니 학습의 궁극적인 목표는 결국 정답 잘 맞출려고 하는건데 당연히 정답 라벨(정답분포)에 대한 cross entropy 변화를 써야되는거 아니야?” 싶었음.
근데 여기서는 학습이 아니라 커리큘럼에 들어갈 애들 선별하는 과정이고, 학습의 목표도 사실 정답을 잘 맞출려고 하는게 아니라 결정경계를 더 정밀하게 다듬는거임.

”그래 좋아. 근데 1,2,3번중에 정답이 1인 문제를 예시로 들어서
강한 모델: 정답 1번(90%), 오답 2번(0.1%), 오답3번(9.9%)
약한 모델: 정답 1번(90%), 오답 2번(5%), 오답3번(5%)
이런 상황이라면, 엔트로피 변화는 존재하니까 커리큘럼에 선별할텐데 정답분포는 둘다 똑같으니까 나중에 훈련할때 힘들게 뽑아놓고 못써먹는거 아니야? 어차피 훈련할때는 정답분포랑 cross-entropy로 훈련하니까 오답분포가 어떻게 변하든 학습에서는 씹힐거아냐?”

싶었는데, $$\frac{\partial L}{\partial z_t[k]}=P_\theta(k\mid x)-\mathbb{I}[k=y]$$ 여서 cross-entropy loss를 쓰고 오답분포에서만 변화가 있는거라고 해도 안씹히고 거기까지 신호가 들어간다고 함!

~~오히려 내 생각대로 선별과정에서 cross-entropy 변화를 썼으면 정답만 맞추는것만 보고 진짜 알짜배기인 결정경계를 어설프게 넘어가는건 못잡았을거임!~~

<div style="display:flex; gap:12px; align-items:flex-end;">
  <figure style="width:74%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig5.png" alt="손그림: 다중분류에서 클래스 개수만큼의 결정 초평면이 있고, 입력 x가 어느 초평면과 가장 가까운지로 로짓이 정해진다는 설명" style="width:100%;">
    <figcaption style="text-align:center; font-size:0.85em; color:gray;">
      Linear층에서 나오는 로짓의 정체
    </figcaption>
  </figure>
  <figure style="width:24%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig6.png" alt="Transformer 디코더 구조도 - 맨 위의 Linear와 Softmax 층이 로짓과 출력 확률을 만듦" style="width:100%;">
  </figure>
</div>

로짓은 자기 클래스 결정초평면과 얼마나 가까운지를 나타내는 값이므로, 오답은 누르고 정답은 마진을 늘리고 하는방식!

**Stage3: training via Logit mixing**

![손그림: P_strong, P_mix, P_weak 분포 곡선과, 로짓 혼합 전(before)과 후(after)의 강한 모델 로짓에 대한 그라디언트 유도](/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig7.png)

$$z_i=\lambda z_{\text{strong}}+(1-\lambda) z_{\text{weak}}$$ 이렇게 로짓을 혼합한걸가지고 학습함.

$$
\begin{align*}
&\text{before}:\frac{\partial L}{\partial z_{strong}} = 
\begin{cases}P_{strong}(y_i \mid  x)-1  \quad (i=k)
\\
 P_{strong}(y_i \mid x) \quad (i \neq k)
\end{cases}

\\

&\text{after}:\frac{\partial L}{\partial z_{strong}} = 
\begin{cases}\lambda\{P_{mixed}(y_i \mid  x)-1\}  \quad (i=k)
\\
\lambda P_{mixed}(y_i \mid x) \quad (i \neq k)
\end{cases}
\end{align*}
$$

기존의 강한모델 분포로만 훈련하면 이미 분포가 포화돼서 학습신호를 받을수 없지만, 이렇게 약한모델을 섞은 로짓을 사용하면 분포가 포화되지 않아 학습신호를 일부($$\lambda$$)만 받게 되긴 하지만 그래도 학습신호가 들어옴.

---

## 5.  Why can weak make strong stronger

왜 작동하는지에 대한 수식유도를 사실 여기서 하는데 위에서 이미 해버려서 이부분은 넘어가고, 이 방법으로 학습하는 과정이 3단계의 상태로 구분된다고 함.

1단계: 증폭 
우리가 의도한대로 약한모델이 혼합분포 $$P_{mix}$$를 효과적으로 약화시켜 강한모델에도 학습신호가 잘 들어감.

2단계: 방어
강한모델이 너무 학습이 잘되어서 더이상 약한모델의 구린 로짓을 넣어도 씹어버림.
아니, 가중평균인데 한쪽이 트롤하면 못막는거 아님? 싶었는데, 생각해보니 가중평균해주는건 둘의 확률분포가 아니라 로짓을 가중평균하는거였음.
그래서 강한모델의 로짓이 너무 커져버리면, 아무리 약한모델이 발목잡아도 softmax를 통과하고나면 효과가 거의 없어져버림…

3단계: 표류
이제 더이상 학습이 안되는데, 소프트맥스는 $$softmax(z+c)=softmax(z)$$ 이런 이동불변성이 있어서 로짓들이 개형을 유지한채로 둥둥 떠다니는 표류가 발생함.
그라디언트가 없어서 명시적으로 미는힘은 없는데, 멈추지도 않아서 무중력상태가 된것처럼 떠다님.
랑주뱅동역학느낌을 생각하면 결정론적힘은 없고 확률론적인 노이즈에 의해 움직이게되는듯.

---

## 6. Experiments

![논문 Table 1: Qwen3-4B-Base, Qwen3-8B-Base, Qwen2.5-3B에서 SFT, UNDIAL, NEFTune, WMSS의 수학 7종·코드 2종 벤치마크 결과](/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig8.png)

다른 SFT계열 학습방법들과 비교해봤을때, 유의미한 성능향상이 일관되게 관찰됨.
베이스라인으로 UNDIAL과 NEFTune을 사용했는데, UNDIAL은 자만을 막기위해 모델이 출력하는 정답로짓을 랜덤하게 깎아버리는거고, NEFTune은 임베딩공간에서 노이즈를 넣어서 일반적이고 강건하게 학습되도록 하는방법임.

![손그림: WMSS는 헷갈렸던 '진짜' 오답 위치의 분포를 키우고, UNDIAL은 정답을 깎아 오답 전체를 고르게 키우는 차이](/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig9.png)

아니, UNDIAL도 그럼 WMSS랑 비슷한거 아냐? 정답을 깎으면 소프트맥스 특성상 오답을 키우는거랑 동일한 효과잖아? 하는 생각이 들었는데, WMSS는 진짜 오답을 키우는거고 UNDIAL은 무지성으로 오답을 키우는거라 전자는 자기가 헷갈렸던 오답을 다시 복기하는 효과였다면 후자는 그냥 아무영영가없는 오답복기시키는느낌.
특히, 어려운 벤치마크일수록 상승폭이 훨씬 두드러지는것을 확인할 수 있음.

<figure style="width:71%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Weak-driven-learning/weak-driven-learning-fig10.png" alt="논문 Table 2: Qwen3-4B-Base의 로짓 통계 - SFT 대비 WMSS는 정답 로짓은 거의 그대로(+0.6%)이고 오답 로짓 평균이 56.9% 감소" style="width:100%;">
</figure>

그리고 예상대로 WMSS는 기존방법인 SFT에 비해 정답로짓을 키우기보다는 오답로짓을 눌러버리는 방식으로 작동하는것을 확인할 수 있었음.
