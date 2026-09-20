---
title: Toolformer 리뷰
date: 2026-09-20 00:36:00 +0900
categories: [AI Paper Reviews, Agents]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>🏃🏻</div>
<div markdown="1" style="flex:1; min-width:0;">

**Toolformer: Language Models Can Teach Themselves to Use Tools**<br>
Date : 2023.2.9<br>
Venue : Neurips oral<br>
Comprehension : 2.7단계

</div>
</div>

## 0. Abstract

LLM이 크기가 커지면서 다양한 과제도 잘하고 좋은데, 단순계산이나 검색같은건 작업에 특화된 초소형모델(Tool)보다도 훨씬 못하는경우가 많아서 LLM에 이런 Tool을 사용하는 방법을 학습시켜주겠다고 함.
특히, 비싼 지도학습이 아니라 자기지도방식으로 학습시키는데 이러니까 다양한 Tool들을 사용할수 있는 보편적인 능력을 기르면서도 LLM의 장점인 언어모델링능력은 유지되었다고 함

ReAct랑 차이점이 헷갈렸는데, ReAct는 프롬프팅이고, Toolformer는 fine-tuning임.
물론 ReAct에서도 fine-tuning실험을 해보긴 했는데, ReAct는 좀 특정 해결패턴?을 알려주는 느낌이라면 Toolformer는 LLM한테 범용적인 Tool사용능력 자체를 만들어주는 느낌임

---

## 1. Introduction

LLM이 엄청난 퍼포먼스를 보이고있긴 하지만, 내부지식을 이용하므로 최신정보에 접근도 못하고, 그것때문에 hallucination도 생기고, 수학계산도 잘 못한다는 한계가 있음.

LLM에 도구 사용능력을 부여하려는 기존의 연구들도 있긴했는데, 대량의 인간주석에 의존하거나 task-specific한 방법들이라 한계가 명확했다고 함.

<figure style="width:47%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Toolformer/toolformer-fig1.png" alt="논문 Figure 1: Toolformer의 예측 예시 - 문장 중간에 QA, Calculator, MT, WikiSearch API 호출과 결과가 삽입된 모습" style="width:100%;">
</figure>

그래서 자기들은 자기지도방식으로 task-agnostic한 Tool사용 훈련방법을 만들어냄.
6.7B 크기의 모델인 GPT-J에 이 방법론대로 fine-tuning 하니까 175B인 GPT-3를 이겼다고 함.

---

## 2. Approach

![논문 Figure 2: 접근법의 핵심 단계 - LM Dataset에서 Sample API Calls, Execute API Calls, Filter API Calls를 거쳐 API 호출이 포함된 데이터셋 생성](/assets/img/ai_paper_reviews/Toolformer/toolformer-fig2.png)

원본데이터셋 $$\mathcal{C}=\{\mathbf{x}^{1}, ... ,\mathbf{x}^{\vert\mathcal{C}\vert}\}$$ 이 들어오면 Sample API Calls → Execute API Calls → Filter API Calls 세 단계의 과정을 거쳐 API호출이 추가된 $$\mathcal{C}^*$$로 변환하고, 이 데이터셋을 통해 모델 $$M$$을 fine-tuning함.

API를 쓸때는 $$\langle API \rangle a_c(i_c) \langle /API \rangle$$ 이렇게 호출하고 표기는 $$c=(a_c,i_c)$$로 하는데, $$a$$는 호출하는 API의 종류이고, $$i$$는 API에 요청하는 쿼리 내용임.

**Sampling API Calls :** 

<figure style="width:57%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Toolformer/toolformer-fig3.png" alt="논문 Figure 3: 질의응답 도구의 API 호출을 생성하게 하는 few-shot 프롬프트 P(x) 예시" style="width:100%;">
</figure>

먼저, 입력데이터 $$\mathbf{x}$$가 있으면, 이런식으로 앞에 Instruction과 few-shot 프롬프트가 붙은 $$P(\mathbf{x})$$ 로 조립함.
($$P$$ 보고 확률인줄알았는데, 알고보니까 그냥 프롬프트라는뜻의 함수임… 하 진짜…🤬🤬 참고로 이 논문에서 확률은 소문자 $$p$$로 표현함)

이제 샘플 $$\mathbf{x}=\{x_1,x_2,...,x_n \}$$ 의 모든 토큰들에 대해 $$p_i=p_M(\langle API \rangle \mid P(\mathbf{x}),x_{1:i-1})$$ 으로 &lt;API&gt;를 생성해서 Tool을 호출할 확률을 예측함.
$$p_i$$가 임계값 $$\tau_s$$를 못넘는건 다 버리고, 개수는 최대 $$k$$개까지만 수집함.

근데 이건 그냥 어떤 토큰에서 API를 호출할지 여부만 정한거라, $$[P(\mathbf{x}),x_{1:i-1},\langle API \rangle]$$ 를 다시 모델에 넣어서 진짜 호출, 즉 실제로 어떤 API에 어떤 쿼리를 넣을지 샘플링하는데, 이때 한개만 하는게 아니라 최대 $$m$$개의 API호출  $$c_i^1,...,c_i^m$$를 얻음.

**Executing API Calls :**

그리고 아까 만들어둔 API 호출들을 실제로 실행해서 결과 $$r$$을 받아옴.

**Filtering API Calls :**

이제 여기서 API 호출이 얼마나 도움이 됐는지 실효성을 평가하는데, 평가방식이 참신함.

$$
L_i(\mathbf{z})=-\sum_{j=i}^n w_{j-i} \cdot \log p_M(x_j \mid \mathbf{z}, x_{1:j-1})
$$

우선 손실을 이렇게 정의하는데, $$\mathbf{z}$$가 주어졌을때 $$i$$번째 토큰 이후의 예측의 손실함수의 가중합임.
즉 $$i$$번째 토큰만 예측하는게 아니라 이후의 생성들에 대해서도 고려하는데, 뒤에서 나오지만 뒤의 5토큰까지 보도록 가중치를 설정해두었다고 함. 그리고 여기서도 Teacher forcing 사용함.
그리고 $$\mathbf{z}$$는 힌트로 뭘 넣을지를 나타낸것인것 같음.

$$
\begin{align*}
&L_i^+=L_i(e(c_i,r_i)) \\
&L_i^-=\min(L_i(\epsilon),L_i(e(c_i,\epsilon)))
\end{align*}
$$

이렇게 API를 썼을때와 쓰지 않았을때를 각각 $$L_i^+,L_i^-$$로 표시하는데 (여기서 $$\epsilon$$은 아무것도 안 넣어준걸 뜻함 ), 쓰지 않았을때의 경우에 결과없이 호출만 했을때의 손실도 넣어준 이유는 CoT처럼 API호출쿼리라는 추론과정 비슷한게 생겨서 발생한 효과까지 감안하기 위함인듯.

그래서, $$L_i^- - L_i^+ \geq \tau_f$$ 이렇게 API를 호출했을때 둘을 비교해서 임계값을 넘길만큼 확실한 이득이 생길때만 효과가 있는 API호출로 간주하고 남김.

**Model Finetuning & Inference**

$$e(c,r)=\langle API \rangle a_c(i_c) \rightarrow r\langle /API \rangle$$ 이제 API호출과 응답결과까지 포함된 데이터셋 $$\mathcal{C}^*$$를 이용해서 fine-tuning을 진행하는데, 당연히 Teacher forcing을 사용하고, 특이하게도 → 이후에 나오는 API 호출결과인 $$r$$도 예측하도록 훈련이 진행됨.

추론시에도 특이한 프로세스가 추가됐는데, 일반적인 모델처럼 생성을 진행하다가, → 토큰을 생성하는순간 생성을 잠깐 멈추고 API를 실행해서 Tool을 사용함. 이후 실행이 완료되면 이어서 생성 진행함.

---

## 3. Tools

![논문 Table 1: 사용한 모든 API의 입력과 출력 예시 (Question Answering, Wikipedia Search, Calculator, Calendar, Machine Translation)](/assets/img/ai_paper_reviews/Toolformer/toolformer-fig4.png)

사용가능한 도구로는 질의응답시스템(`QA`), 계산기(`Calculator`), 위키백과검색(`WikiSearch`), 기계번역(`MT`), 달력(`Calendar`) 이렇게 5가지를 지원함.

질의응답은 11B의 Atlas라는 모델을 사용하고, 기계번역은 0.6B의 NLLB라는 모델을 사용함.
나머지는 신경망이 아니라 그냥 파이썬 스크립트나 검색엔진같은 규칙기반 시스템임.

---

## 4. Experiments

제안한 방법론이 의도한대로 효율적으로 잘 작동하는지 확인함.
다양한 downstream task에서의 성능을 실험해보고, perplexity를 통해 원래 LLM의 언어모델링역량이 잘 보존되었는지도 확인함.
마지막으로 모델을 scaling했을때 도구사용능력이 어떻게 변하는지도 실험해봄.

### 4.1 Experimental setup

원본 데이터셋 $$\mathcal{C}$$로는 CCNet 이라는 일종의 corpus를 사용해서 $$\mathcal{C}^*$$를 만들어냄.
그리고 아까 슬쩍 넘어간 가중치 $$w$$는

$$
\begin{align*}
&w_t = \frac{\tilde{w_t}}{\sum_{s \in \mathbb{N}} \tilde{w_s}}  \quad \text{where } \tilde{w_t}=\max(0, 1-0.2t)\\ &\Rightarrow \quad w_t = \frac{\tilde{w_t}}{1+0.8+0.6+0.4+0.2} =\frac{\max(0,1-0.2t)}{3}
\end{align*}
$$

이렇게 정의된다고 함.

### 4.2 Downstream Tasks

<div style="display:flex; gap:12px; align-items:flex-start;">
  <figure style="width:49%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Toolformer/toolformer-fig5.png" alt="논문 Table 3: LAMA 부분집합(SQuAD, Google-RE, T-REx) 결과" style="width:100%;">
  </figure>
  <figure style="width:49%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Toolformer/toolformer-fig6.png" alt="논문 Table 4: 수학 추론 벤치마크(ASDiv, SVAMP, MAWPS) 결과" style="width:100%;">
  </figure>
</div>

Toolformer의 위력을 확인해기 위해  tool이 도움이 되는 downstream task들에서 실험해봄.
tool 종류대로 벤치마크도 다양하게 세팅하고 실험했는데, 전 영역에서 비슷한 라이트급들은 학살수준으로 압도하고, 20배 이상 큰 GPT-3 을 이기는 경우도 많았음.

### 4.3 Language Modeling

<figure style="width:72%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Toolformer/toolformer-fig7.png" alt="논문 Table 8: WikiText와 CCNet에서 GPT-J, GPT-J + CC, Toolformer (disabled)의 perplexity" style="width:100%;">
</figure>

Toolformer가 뛰어난건 확인해서 뿌듯한데, 뭔가 그 대가로 LLM의 언어모델링 역량을 희생당한게 아닌지 걱정됨
그래서 &lt;API&gt; 토큰생성확률이 강제로 0으로 거세된 Toolformer(disabled)를 사용해서 테스트해봤더니 다행히 아무 손해없이 언어모델링도 잘 했음

### 4.4 Scaling Laws

<figure style="width:80%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Toolformer/toolformer-fig8.png" alt="논문 Figure 4: 모델 크기에 따른 LAMA, 수학, QA 벤치마크 평균 성능 - Toolformer, Toolformer (disabled), GPT-3 비교" style="width:100%;">
</figure>

너무 좋은 결과가 나와서 해피한데, 이게 어느정도 크기의 모델부터 잘 먹히는지도 실험함.
실험결과, 베이스라인에 비해 성능이 나오기 시작하는 시점을 보니까 역시 너~무 작은 모델은 멍청해서 Toolformer방법론을 써도 잘 하질 못하고, 한 775M정도의 모델부터 베이스라인에 비해 성능이 나오기 시작한다고 함.

---

## 5. Analysis

<figure style="width:74%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Toolformer/toolformer-fig9.png" alt="논문 Table 9: 디코딩 시 k 값에 따른 T-REx, WebQS 성능과 API 호출 비율" style="width:100%;">
</figure>

먼저, Top-k 디코딩전략을 분석함.
Toolformer가 API를 사용할때, 꼭 &lt;API&gt; 토큰이 선택됐을때만 하는게 아니라 Top-k개의 후보군 안에 &lt;API&gt; 토큰이 있을때 실행하는 방식을 사용했는데, k를 올리니까 호출한 문제 비율도 올라가고 성능도 약간 상승함.

![논문 Table 10: 필터링 기준값(L- 빼기 L+) 순으로 정렬한 API 호출 예시와 유용성 여부](/assets/img/ai_paper_reviews/Toolformer/toolformer-fig10.png)

다음으로,  $$L_i^--L_i^+ \geq \tau_s$$를 통해 API를 사용했을때 유용할지 판단하자는 논리가 실제로도 맞는논리인지 정성적인 분석을 진행했는데, 실제로 값의 차이가 높을수록 API가 유용한 정보를 제공하는게 맞다는것을 확인함.

---

## 6. Related Work

기존 방법론들과 차별점을 정리함.
언어모델 사전학습시 추가적인 정보를 제공해서 똑똑하게 만드려는 시도는 있었지만 Toolformer처럼 필요할때만 받는게 아니라 무조건 추가정보를 퍼먹여준다는점, 
도구 사용 훈련측면에서는 기존의 방법론들은 대량의 인간라벨링에 의존하거나 특정 downstream task에 맞춰진 방법이라는점을 지적함.

확실히 Bootstrapping을 통해 자신이 만든 유용한 데이터로 pre-training 단계부터 범용적인 도구사용능력을 길러주는 scalable한 방법론이라는 측면에서 차별점이 뚜렷한것같음.

---

## 7. Limitations

훌륭한 방법론이지만, 존재하는 한계점도 고백함.
가령 인간은 퀴즈를 풀기위해서 위키백과를 보다가 단어를 모르거나 외국어로 되어있으면 단어뜻을 검색하거나 번역기를 사용함.
근데 Toolformer는 도구를 연쇄적 상호작용하면서 사용하지 못해서 사람처럼 DFS를 하지 못하고, 첫 Call에서 원큐안에 해결해야함.

또한, 프롬프트에도 매우 민감해서 입력이 조금만 달라져도 API 호출여부가 불안정해지고, 데이터효율성도 떨어진다는 문제가 있다고 함.

---

## 8. Conclusion

Toolformer는 스마트한 샘플링을 통해 얻은 데이터셋을 자기지도방식으로 fine-tuning함으로서 도구들을 범용적으로 사용하는 능력을 갖게된 훌륭한 모델이라고 마무리함.

---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>😲</div>
<div markdown="1" style="flex:1; min-width:0;">

**느낀점**<br>
상당히 참신하고 재밌는 방법론이었음.<br>
특히 API 요청을 만들어내는 로직, API 요청이 쓸모있는지 판단하는 로직이 상당히 재밌었음.<br>
거기다가 참신함뿐만 아니라 도구를 잘 쓰는, 실제로 상당히 쓸모있는 모델이 나왔다는점이 진짜 중요.<br>
도구의 DFS가 안된다는점이 아쉽지만, 이건 먹음직스러운 주제라서 후속논문들이 많이 달려들어서 연구한다고 함.

</div>
</div>
