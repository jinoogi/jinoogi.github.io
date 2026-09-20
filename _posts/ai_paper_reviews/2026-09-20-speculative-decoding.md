---
title: Speculative Decoding 리뷰
date: 2026-09-20 00:23:00 +0900
categories: [AI Paper Reviews, NLP & LLM]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Fast Inference from Transformers via Speculative Decoding**<br>
Date : 2022.11.30<br>
Venue : ICML Oral

</div>
</div>

## 0. Abstract

![Transformer 인코더-디코더가 매 타임스텝마다 토큰을 하나씩 생성하는 auto regressive 디코딩 과정 애니메이션](/assets/img/ai_paper_reviews/Speculative-Decoding/speculative-decoding-fig1.gif)

이 논문은 auto regressive하던 기존의 언어모델이 하나씩 추론해야하는 특성상 모든 토큰이 출력되기까지 오랜 시간이 걸린다는 약점을 보완하는 speculative decoding이라는 방법을 소개함
speculative 이라는 말 뜻 자체가 “추측에 근거한” 이라는 뜻인데, 구체적으로는 메인 모델이 아니라 소형 모델로 먼저 토큰 예상을 해놓고, 그걸로 병렬적인 토큰 생성을 하는 방법인듯
일종의 캐싱방법과 유사해보임

![Speculative decoding 개요: Draft model이 토큰을 순차 생성(Step1)한 뒤 Target model이 병렬로 검증(Step2)](/assets/img/ai_paper_reviews/Speculative-Decoding/speculative-decoding-fig2.png)

I → I am

I am→ I am a

I am a → I am a boy

기존에는 한 타임스텝당 저 작업을 하나씩만 할 수 있었는데, 

미리 I am a boy 를 소형근사모델(Approximation model)이 예상해놓으면

I → I am

I am→ I am a

I am a → I am a boy

원래 모델(Target model)로 이 과정을 병렬적으로 돌릴 수 있으니까…

이건 아키텍쳐나 모델을 다시 학습시킬 필요도 없고,  속도는 2~3배 빨라지면서도 확률분포,출력결과는 완전히 동일하게 유지되고, 아키텍쳐나 모델학습을 다시 시킬필요도 없이 간단하게 적용 가능하다고 함

---

## 1. Introduction

추론비용을 줄이는 방식으로 양자화, 증류같은 모든 입력에 대해 전체적으로 적용되는 방법이 있고, 생성단계나 입력의 난이도에 따라 추론비용을 줄이는 적응적 방법도 있음

여기서는 어떤 추론단계는 어렵고 어떤 단계는 쉽다는 관찰에서 출발하는 적응적 방법론을 사용

또한, 연산량이 아니라 메모리 대역폭이나 통신에서 bottleneck이 발생한다는점을 관찰하고, GPU가 idle하지 않도록 병렬적인 연산을 하는 방법론을 제안

이게 앞서 말한 speculative decoding이고, 근사모델 $$M_q$$를 통해 sample sequence를 먼저 생성하고 이걸 타겟모델 $$M_p$$가 병렬적으로 검증하는 방법임

![논문 Figure 1: 근사모델이 제안한 토큰(초록)과 타겟모델이 거부(빨강)·수정(파랑)한 토큰을 줄 단위로 보여주는 예시](/assets/img/ai_paper_reviews/Speculative-Decoding/speculative-decoding-fig3.png)

이 방식을 사용하면, 훨씬 시간측면에서 효율적인 추론이 가능함
첫번째줄을 보면, 원래 target model 만 썼을땐 5스텝 실행되어야했던게 한 스텝만에 되는걸 확인할 수 있음

---

## 2. Speculative decoding

### 2.1. Overview

$$p(x\vert x_{<t})$$는 target model이 출력하는 다음 토큰의 확률분포, $$q(x\vert x_{<t})$$는 approximation model이 출력하는 다음 토큰의 확률분포임

### 2.2. Standardized sampling

argmax, top-k, top-p 방식 모두 standard sampling으로 일반화해 표현 가능하다는 이야기

### 2.3. Speculative sampling

<figure style="width:56%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Speculative-Decoding/speculative-decoding-fig4.png" alt="논문 Algorithm 1: SpeculativeDecodingStep 의사코드" style="width:100%;">
</figure>

target model과 approximation model은 서로 다른 시스템이라 확률분포 $$p(x\vert x_{<t})$$, $$q(x\vert x_{<t})$$가 다르지만, 통계적 기법을 통해 결국 둘의 확률분포를 동일하게 만들 수 있다는 이야기

알고리즘의 핵심을 살펴보면
$$q(x) \leq p(x)$$ 이면 샘플 유지, $$q(x) > p(x)$$이면 $$1-\frac{p(x)}{q(x)}$$의 확률로 거부하고 다시 샘플링하는 방식.
다시 샘플링할때는 $$p'(x)=\mathrm{norm}(\max(0,p(x)-q(x)))$$ 으로부터 샘플링하기
이렇게 하면 동일한 분포를 갖게 되는게 증명되어있다고 함

---

## 3. Analysis

$$\gamma$$ : 한번에 추측하는 토큰 개수, 
$$\alpha$$ : 근사모델 예측이 채택될 평균 확률, 
$$c$$ : target모델 대비 근사모델 한번 돌릴때 드는 시간 비율

walltime(실제 타겟모델이 추론에 걸리는 시간)은 $$\alpha$$가 높을수록, $$c$$가 낮을수록, $$\gamma$$값이 최적일때 가장 빨라짐 

근사모델을 선택할때는, 크기가 두자릿수정도 적은 모델을 선택하는것이 가장 $$\alpha,c$$가 좋았다고 함

---

## 4. Experiments

<figure style="width:70%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Speculative-Decoding/speculative-decoding-fig5.png" alt="논문 Table 2: T5-XXL 11B를 타겟으로 근사모델, temperature, γ에 따른 α와 속도 향상 결과" style="width:100%;">
</figure>

실제 실험으로 이 speculative decoding이 얼마나 효율적인지를 증명함

Target model로는 T5-XXL이라는 110억 파라미터 모델을 사용했고, approximation model로는 위의 표처럼 T5-small(0.77억), T5-base(2.5억), T5-large(8억) 모델을 사용함.

그 결과 샘플링방법은 argmax(Temp=0)이 가장 효율적이고, 모델은 T5-small이 가장 효율적이었다고 함

---

## 5. Related works

skip

---

## 6. Discussion

그래서 이 논문에서 제시하는 speculative decoding은, T5-XXL에서 2~3배의 성능 향상을 보였다고 함
특히 다른 추론속도 향상 방법론과 달리, 이 방법은 모델아키텍쳐 변경이나 재학습이 필요없고 출력분포가 완전히 동일하게 유지된다는 장점이 있음

그러나 연산량은 충분한데 메모리나 통신이 병목인경우에 연산량을 대가로 사용하는 방법론이라, 연산량이 부족한 경우에는 사용할수 없다는 한계점은 있음
