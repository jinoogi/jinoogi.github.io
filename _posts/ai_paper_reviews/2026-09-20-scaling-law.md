---
title: Scaling law 리뷰
date: 2026-09-20 00:26:00 +0900
categories: [AI Paper Reviews, NLP & LLM]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Scaling Laws for Neural Language Models**<br>
Date : 2020.1.23<br>
Venue : arXiv

▶ [챗지피티는 집에서 만들지 말고 사서 쓰세요 \| 스케일링 법칙](https://www.youtube.com/watch?v=QkPeMzr3Qz4)

</div>
</div>

<details markdown="1">
<summary><strong>Power law란?</strong></summary>

어느 변수가 단항식처럼 다른 변수와 거듭제곱의 관계로 표현되는 관계<br>
지수관계와는 다른게, 멱관계는 밑이 변수인 관계고, 지수관계는 지수가 변수인 관계임

<div style="display:flex; gap:16px; align-items:flex-start;">
<div markdown="1" style="width:49%;">

멱관계 (power)

![멱관계 예시: y=x^2 그래프](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig1.png)

$$
y=x^2
$$

</div>
<div markdown="1" style="width:49%;">

지수관계 (exponential)

![지수관계 예시: y=2^x 그래프](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig2.png)

$$
y=2^x
$$

</div>
</div>

</details>

<details markdown="1">
<summary><strong>수익체감 지점</strong></summary>

<figure style="width:65%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig3.png" alt="처음에 급격히 감소하다가 완만해지는 곡선 - 엘보우 지점이 수익체감 지점" style="width:100%;">
</figure>

수익체감 지점: 파레토커브 상에서 Trade-off 관계를 고려한 최적점으로, 보통 엘보우 지점을 찾음

</details>

<details markdown="1">
<summary><strong>논문 구조 요약</strong></summary>

이 논문은 내용도 많고 나열식이라 읽기가 너무 진빠짐…<br>
어떤장을 볼지 선택하고 일부만 자세히 볼 예정

- **1장: Introduction (소개)**
    - 전체 연구의 **요약본**입니다. 논문의 핵심 발견과 최종 공식들을 미리 보여주며, 앞으로 어떤 내용을 다룰지 안내합니다. (1.1 Summary, 1.2 Summary of Scaling Laws)
- **2장: Background and Methods (배경 및 방법론)**
    - **'어떻게 실험했는가?'**에 대한 부분입니다. 어떤 모델(Transformer) 구조를 사용했는지, 파라미터 수(N)나 연산량(C)을 어떻게 계산했는지, 어떤 데이터셋(WebText2)을 썼는지 등 실험의 배경과 방법을 설명합니다.
- **3장: Empirical Results and Basic Power Laws (실험 결과 및 기본 멱법칙)**
    - 가장 기본적인 실험 결과들을 보여주는 장입니다. 모델 크기(N), 데이터셋 크기(D), 연산량(C) 각각의 요소가 성능에 미치는 영향을 개별적으로 보여주는 **세 가지 기본 멱법칙**을 그래프와 함께 제시합니다.
- **4장: Charting the Infinite Data Limit and Overfitting (과적합 법칙 분석)**
    - **'과적합'** 현상을 집중적으로 파고드는 장입니다. 모델 크기(N)와 데이터셋 크기(D)가 동시에 작용할 때 어떤 일이 일어나는지, 즉 L(N,D) 공식을 유도하고 실험으로 증명합니다.
- **5장: Scaling Laws with Model Size and Training Time (학습 곡선 법칙 분석)**
    - **'학습 과정'** 자체를 집중적으로 분석하는 장입니다. 모델 크기(N)와 학습 스텝(S)의 관계, 즉 L(N,S) 학습 곡선 공식을 다룹니다. 저희가 길게 이야기했던 **임계 배치 크기(Bcrit)**와 **Smin**의 개념이 여기서 자세히 다뤄집니다.
- **6장: Optimal Allocation of the Compute Budget (최적의 예산 분배)**
    - 이 논문의 **가장 실용적인 결론**이 담긴 장입니다. 4장과 5장의 분석 결과를 총동원하여, "주어진 컴퓨팅 예산을 어떻게 모델 크기, 배치 크기, 스텝 수에 분배해야 최적인가?"에 대한 답을 수식과 그래프(Figure 3)로 제시합니다.
- **7장 & 8장: Related Work, Discussion (관련 연구 및 토의)**
    - 연구의 의미를 해석하고 다른 연구들과 비교하며, 발견한 법칙들의 한계와 향후 연구 방향 등을 논의합니다.

</details>

## 0. Abstract

여러 요소들이 언어모델의 성능에 어떤식으로 영향을 미치는지 분석해본 논문.

1. 데이터셋의 크기, 컴퓨팅 자원에 따라 어떻게 변화하는지 Cross entropy loss를 이용해서 실험적으로 분석해본 결과, Power law의 관계가 있다는것을 밝히고 수식으로 표현함.
2. 네트워크의 깊이나 폭이 크게 성능에 영향을  끼치지 않는다는 사실을 밝혀냈음
3. 과적합의 정도가 $$\frac{\vert\mathrm{model}\vert}{\vert\mathrm{dataset}\vert}$$과 관련이 있음을 밝히고, 수식으로 표현함.
4. 학습속도가 $$\vert\mathrm{model}\vert$$ 과 관련이 있음을 밝히고, 수식으로 표현함.
5. 큰 모델일수록 데이터 효율이 높음을 밝히고, 최적의 학습 전략을 제시함

![논문 부록 A: power law 요약 표 (Table 4 수식 정리, Table 5 피팅된 상수값, Table 6 compute-efficient 학습의 최적 파라미터)](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig4.png)

---

## 1. Introduction

### 1.1. Summary

**1. 성능은 규모에 강하게 의존하고, 형태에는 약하게 의존한다**
모델은 주로 모델 파라미터 수 $$N$$, 데이터셋 크기 $$D$$, 학습에 사용된 컴퓨트 $$C$$에 크게 좌우되며, 그 외의 아키텍쳐 하이퍼파라미터(깊이나 너비같은)는 합리적인 범위 내에서는 성능에 거의 영향을 못줬다고 함

**2. 매끄러운 거듭제곱법칙**

![논문 Figure 1: compute, 데이터셋 크기, 파라미터 수 각각에 대해 test loss가 power law로 감소](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig5.png)

나머지 요소가 병목을 일으키지 않는 상황에서의 순수한 영향을 분석해보면, 성능은 $$N,D,C$$ 각각과 거듭제곱 관계를 가졌다고 함

**3. 과적합의 보편성**
위의 매끄러운 거듭제곱법칙에서 봤듯 병목없이 $$N,D$$를 함께 키우면 성능이 매끄럽게 거듭제곱으로 올라가지만, 한쪽이 병목이 된 상태에서 나머지 한쪽을 올리면 성능 저하가 일어남.
이때의 성능 저하는 $$N^{0.74}/D$$로 표현되며, 이 수식의 뜻을 생각해보면 모델크기가 8배 늘어날때마다 데이터를 5배 늘리면 과적합이 안생긴다는 말임

**4. 학습의 보편성**
학습곡선은 모델 크기와 거의 무관하게 매끄러운 power law를 따르므로, 조금만 봐도 개형을 예측하기 쉽다고 함.

**5. 전이학습은 원래성능과 함께 향상된다**

![논문 Figure 8: 다른 데이터 분포에 대한 일반화 성능이 모델 크기, 학습 분포에서의 loss와 함께 매끄럽게 향상](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig6.png)

pre-training같이 미리 훈련해둔 모델을 전이학습시켜도, 원래의 pre-train 모델 성능을 평행이동시킨것에 지나지 않는다고 함.
다만 전이학습 도메인마다 그 평행이동 오프셋이 조금씩 달라질 뿐

**6. 샘플 효율성**

![논문 Figure 2: 큰 모델일수록 같은 성능에 필요한 샘플이 적고, compute-efficient 학습은 수렴 훨씬 전에 멈춤](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig7.png)

![논문 Figure 4: 데이터셋 크기와 모델 크기에 따른 loss(왼쪽), 모델 크기와 학습 스텝에 따른 학습 곡선(오른쪽)](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig8.png)

큰 모델이 작은모델보다 훨씬 샘플이 덜 있어도 된다고 함 (물론 상식적인 범위 내에서)

**7. 수렴은 비효율적이다**

![논문 Figure 3: compute가 늘어날 때 모델 크기, 배치 크기, 학습 스텝에 배분되는 비중](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig9.png)

필요한 컴퓨팅은 대략적으로 $$C \approx N\times B \times S$$ 이렇게 모델 크기와 배치 크기와 스텝 수로 표현되는데, 위의 표는 각 요소가 저 컴퓨팅 곱셈관계에서 얼마나 비중을 차지해야 하는지 시각화해놓았음.
컴퓨팅 $$C$$가 정해져있을때, 작은모델을 골라 끝까지 수렴시키는데 쓰는것보다 큰 모델을 골라 덜 수렴시키는게 훨씬 낫다고 함

**8. 최적 배치크기**
최적 배치 크기가 손실값에 반비례하는 power law를 따른다는 사실을 밝혀냈다고 함

### **1.2. Summary of Scaling Laws**

![논문 Figure 1 (재게시): compute, 데이터셋 크기, 파라미터 수에 대한 test loss의 power law](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig10.png)

**병목없고 수렴시킬 때, $$N$$에 관한 매끄러운 power law**

$$
L(N)=\left(\frac{N_c}{N}\right)^{\alpha_N} \quad , \text{where } \alpha_N \approx 0.076,\: N_c\approx8.8\times 10^{13}
\tag{1.1}
$$

**병목없고 조기종료시킬때, $$D$$에 관한 매끄러운 power law**

$$
L(D)=\left(\frac{D_c}{D}\right)^{\alpha_{D}} \quad , \text{where }\alpha_D \approx 0.095, \;D_c \approx 5.4 \times 10^{13}
\tag{1.2}
$$

**제한된 컴퓨팅에서 병목없고 최적의 학습전략(모델과 데이터셋 비율)일때, $$C$$에 관한 매끄러운 power law**

$$
L(C_{min})=\left(\frac{C_c^{min}}{C_{min}}\right)^{\alpha_C^{min}} \quad , \text{where } \alpha_C^{min} \approx 0.050,\: C_c^{min}\approx3.1\times 10^{8}
\tag{1.3}
$$

**최적 배치크기**

![Large-Batch Training 논문 Figure 6: SVHN에서 배치 크기별 학습 속도와 학습 효율](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig11.png)

![Large-Batch Training 논문 Figure 7: 시간 효율과 연산 효율 사이의 파레토 프런티어와 noise scale 비교](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig12.png)

“An Empirical Model of Large-Batch Training” 이라는 논문에서 나온 내용으로, 배치크기가 커지면 훈련시간은 짧아지지만 데이터 효율성이 떨어지고, 배치크기가 작아지면 데이터 효율성은 좋아지지만 시간이 너무 오래걸려서 속도/효율 트레이드오프 파레토 커브상에서의 최적 배치크기를 구했더니 

$$
B_{crit}(L)=\frac{B_*}{L^{1/\alpha_B}} \quad, \text{where } B_*\approx2\times10^8, \alpha_B \approx 0.21
\tag{1.4}
$$

가 나왔다고 함

**학습 완료시 이론적 최대 성능**

<figure style="width:79%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig13.png" alt="데이터셋 토큰 수와 모델 크기에 따른 loss 그래프 (Loss vs Model and Dataset Size)" style="width:100%;">
</figure>

$$
L(N,D)=\left[\left(\frac{N_c}{N}\right)^{\frac{\alpha_N}{\alpha_D}}+\frac{D_c}{D}\right]^{\alpha_D} 
\tag{1.5}
$$

$$N,D$$가 주어졌을때, 모델의 이론적 최고성능(early stopping 사용시)이 어느정도일지 모델링 가능

**학습 과정에서의 스텝별 이론적 최대 성능**

$$
L(N,S)=\left( \frac{N_c}{N} \right)^{\alpha_N}+\left( \frac{S_c}{S_{min}(S)} \right)^{\alpha_S},\tag{1.6} \\ \text{where } S_{min}(S)=\frac{S}{1+B_{crit}(L)/B}, \;S_c\approx 2.1\times 10^3,\; \alpha_S \approx 0.76
$$

**제한된 컴퓨팅 내에서의 최적의 자원 분배**

$$
N \propto C^{\alpha^{min}_C/\alpha_N}, \quad B \propto C^{\alpha^{min}_C/\alpha_B}, \quad S \propto C^{\alpha^{min}_C/\alpha_S}, \quad D=B \cdot S \tag{1.7}
$$

$$
\text{where} \quad \alpha^{min}_C=1/\left( \frac{1}{\alpha_S}+\frac{1}{\alpha_B}+\frac{1}{\alpha_N} \right) \tag{1.8}
$$

### 1.3. Notation

일단 스킵

---

## 2. Background and Method

### 2.1. Parameter and Compute scaling of transformers

<div style="display:flex; gap:12px; align-items:center;">
  <figure style="width:38%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig14.png" alt="원본 Transformer 인코더-디코더 구조도" style="width:100%;">
  </figure>
  <figure style="width:60%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig15.png" alt="Multi-head attention에서 입력 X에 Q, K, V 가중치를 곱하고 결과를 이어붙여 W^O를 곱하는 과정" style="width:100%;">
    <figcaption style="text-align:center; font-size:0.85em; color:gray;">
      Q,K,V,O matrix
    </figcaption>
  </figure>
</div>

![논문 Table 1: Transformer 연산별 파라미터 수와 토큰당 FLOPs 추정](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig16.png)

**파라미터 계산**
$$W_Q,W_K,W_V$$ 모두 입력값($$d_{model}$$)을 어텐션벡터($$d_{attn}$$)로 바꾸는 행렬이므로 크기는 각각 $$d_{model}\times d_{attn}$$$$W_O$$는 어텐션벡터($$d_{attn}$$)를 입력값($$d_{model}$$)으로 바꾸는 행렬이므로, 크기는 $$d_{attn}\times d_{model}$$
그래서 어텐션 모듈은 $$4d_{attn} d_{model}$$
(참고로 멀티헤드 어텐션이면 싱글헤드가 여러개 있는게 아니라, 싱글헤드를 각 헤드가 나눠갖는거임)

Feed forward MLP에서는 hidden이 한 층이므로, 크기는 $$d_{model}\times d_{ff}+d_{ff}\times d_{model}$$
그래서 MLP 모듈은 $$2d_{ff} d_{model}$$

일반적인 Transformer구조에서는 보통 $$d_{ff} \approx 4d_{model}, d_{attn} \approx d_{model}$$ 인 경우가 많아서, 
 $$N \approx 12 \times n_{layer}\times d^2_{model}$$로 간단히 근사 가능

**FLOPs 계산**
플롭스는 보통 행렬의 파라미터 수 x 2인경우가 많아서, 표의 좌측에 2를 곱하면 된다고 생각하면 되고, 비슷한 과정을 거쳐 $$C_{forward} \approx 2N+2n_{layer}n_{ctx}d_{model}$$이라고 함

### 2.2. Training Procedures & 2.3. Datasets

대충 훈련에 필요한 하이퍼파라미터, 데이터셋 설명함

---

## 3. Empirical results and basic power laws

이 장에서는 Scaling law를 분석하기 위해 다양한 요인들의 Scale들을 변화시키며 모델을 학습시켜봄

- 모델 크기: 임베딩을 제외한 0.77B ~ 1.5B 크기의 파라미터
- 데이터셋 크기: 0.22억 토큰~ 230억 토큰
- 모델 형태: depth, width, attention head 수, feed forward 차원
- context 길이: 보통 1024이지만 일부는 더 짧게
- 배치 크기: 보통 $$2^{19}$$지만 일부는 다양하게 함

### 3.1. **Approximate Transformer Shape and Hyperparameter Independence**

![논문 Figure 5: 파라미터 수를 고정하면 모델 형태(feed-forward 비율, aspect ratio, head 차원)는 성능에 거의 영향을 주지 않음](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig17.png)

모델 파라미터 크기 $$N$$을 고정시킨 상태로 $$d_{ff},d_{model}$$같은 차원이나, 레이어 수  $$n_{layer}$$, 헤드 수 $$n_{head}$$를 바꿔봤지만 성능에 별로 차이가 없었다고 함

### 3.2. **Performance with Non-Embedding Parameter Count $$N$$**

![논문 Figure 6: 임베딩 파라미터를 포함했을 때(왼쪽)와 제외했을 때(오른쪽)의 파라미터 수 대비 test loss](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig18.png)

파라미터 크기 $$N$$을 바꿔보면서 실험해본 결과, 위의 개형과 같은 관계가 발견되었으며, 오른쪽처럼 임베딩 파라미터를 빼고 보면 더욱 선명하고 매끄러운 $$L(N) \approx \left( \frac{N_c}{N}\right)^{\alpha_N}$$ 관계가 보인다고 함. 

<figure style="width:63%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig19.png" alt="여러 데이터셋(WebText2, Books, Wikipedia 등)에서 파라미터 수에 따른 test loss" style="width:100%;">
</figure>

또한, 이 모델들은 WebText2 라는 거대 데이터셋으로 학습되었지만, 다른 데이터셋들을 써서 평가해보면 마찬가지로 이렇게 거의 같은 양상을 보였다고 함

**3.2.1. Comparing to LSTMs and Universal Transformers**

![논문 Figure 7: 파라미터 수에 따른 Transformer와 LSTM 성능 비교(왼쪽), context 내 토큰 위치별 loss(오른쪽)](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig20.png)

Transformer 구조와 LSTM 구조도 비교해보았는데, 좌측그림에서 볼 수 있듯 파라미터가 커지면 LSTM와 Transformer 성능 격차가 더 커지는걸 볼 수 있음.
우측그림에서는 긴 context에서의 token loss인데, Transformer는 문장이 길어져도 앞선 문장들이 주는 문맥정보가 많아지므로 앞의 정보들을 잘 써먹어 뒤의 토큰을 점점 잘 예측하게 되지만, LSTM은 100토큰이 넘어가면 앞의 문장들에 대한 문맥정보를 더이상 기억하지 못하고 못써먹어서 loss가 평평하게 유지되는 현상을 보임

**3.2.2. Generalization Among Data Distributions**

<figure style="width:63%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig21.png" alt="학습 분포에서의 test loss와 다른 분포에서의 loss 사이의 선형 관계" style="width:100%;">
</figure>

pre-train은 web2text로 하고 다른 데이터셋들로 평가해봐도, 다른 데이터셋으로 평가한 loss가 이 pre-train 데이터셋에서 평가한 loss랑 선형으로 직결된다는 이야기

### **3.3 Performance with Dataset Size and Compute**

<figure style="width:49%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig22.png" alt="데이터셋 크기에 따른 test loss의 power law 그래프" style="width:100%;">
</figure>

먼저, 데이터셋 크기 $$D$$와 손실 추세를 실험으로 관찰해보니, 위의 그림처럼 $$L(D) \approx \left( \frac{D_c}{D} \right)^{\alpha_D}$$ 의 관계가 보임

<figure style="width:55%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig23.png" alt="compute에 따른 test loss의 power law 그래프" style="width:100%;">
</figure>

다음으로 컴퓨팅에 대한 손실 추세를 실험해봄
순전파와 역전파연산을 모두 포함해 계수 6을 곱하면, 컴퓨팅은 $$C \approx 6NBS$$ 으로 근사됨
그래서 정해진 $$C$$ 내에서 $$B$$는 고정시키고 $$N,S$$ 조합을 이리저리 바꿔보며 제일 잘나온 Loss값을 plot함
그렇게 해보니 $$L(C) \approx \left(\frac{C_c}{C}\right)^{\alpha_C}$$의 관계가 보임

---

## **4. Charting the Infinite Data Limit and Overfitting**

이 장에서는 모델 크기 $$N$$과 데이터셋 크기 $$D$$를 동시에 변환시켜보며 Scaling law를 모델링해봄
실험적으로 유도되며, 그 결과가 식 (1.5)처럼 나온다는걸 밝힐거임

### 4.1. Proposed $$L(N,D)$$  Equation

해당 Scaling law를 수식으로 모델링할때, 다음과 같은 3가지 가정을 바탕으로 기초적인 뼈대를 먼저 잡음

1. 어휘 크기나 토크나이징 방식 변화는 손실 전체를 rescale 할것이다
→ $$N,D$$ 에는 보정상수가 붙을것이다
2. $$D$$를 무한대로 보내면 전체 손실은 $$L(N)$$으로 수렴할것이고, $$N$$을 무한대로 보내면 전체 손실은 $$L(D)$$으로 수렴할것이다
3. $$D$$를 무한대로 보냈을때 $$L(N,D)$$ 는 해석적이어야한다
→ 과적합은 $$1/D$$에 비례해야한다는 통계적 가설이 있다고 함

$$
L(N,D)=\left[\left(\frac{N_c}{N}\right)^{\frac{\alpha_N}{\alpha_D}}+\frac{D_c}{D}\right]^{\alpha_D} 
\tag{1.5}
$$

그 가정들을 바탕으로 위와같은 손실 모델을 제안함

### 4.2. Results

![논문 Figure 9: 데이터 크기 병목에 따른 loss(왼쪽)와 N^(αN/αD)/D에 따른 과적합 정도(오른쪽)](/assets/img/ai_paper_reviews/Scaling-law/scaling-law-fig24.png)

실험을 진행해서 피팅해본 결과, 위의 좌측사진에서 볼 수 있듯 앞서서 제안한 손실모델이 매우 잘 맞아떨어지는것을 확인했음.

이어서 과적합을 측정하는 식을 정의하고 모델링해봄

$$
\delta L(N,D) \equiv \frac{L(N,D)}{L(N,\infty)}-1 \tag{4.2}
$$

과적합의 정도를 $$\delta L$$ 로 정의하고 , 과적합이 전혀 나지 않은 성능과의 비율로 표현

$$
\delta L \approx \left( 1+ \left( \frac{N}{N_c} \right)^{\frac{\alpha_N}{\alpha_D}}\frac{D_c}{D} \right)^{\alpha_D}-1 \tag{4.3}
$$

식 (1.5)로 유도하면 위와 같은 수식으로 표현되고, 테일러급수로 표현했을때 $$D$$ 가 클 경우 이 식은 $$1/D$$항으로 근사될 수 있음.
실험결과, 우측 사진처럼 근사화된 과적합 모델도 실제 현상과 매우 잘 맞아떨어지는것을 확인했다고 함
