---
title: Diffusion 리뷰
date: 2026-09-20 00:10:00 +0900
categories: [AI Paper Reviews, CV & Multimodal]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Denoising Diffusion Probabilistic Models**<br>
Date : 2020.12.16<br>
Venue : NeurIPS Main<br>
Comprehension : 1.6단계

▶ [But how do AI images and videos actually work? \| Guest video by Welch Labs](https://youtu.be/iv-5mZ_9CPY?si=QZHHJzzpb3Hcu_m2)

</div>
</div>

## 0. Abstract

확산 확률모델을 이용해 고품질 이미지 생성모델을 만듦.

---

## **1. Introduction**

당시에는 생성모델 분야에서 GAN, VAE, auto-regressive 모델, flow 모델들이 좋은 성능을 보이며 주류 모델로 경쟁하고있었다고 함.

확산모델은 원본 데이터를 점점 노이즈화해서 신호를 소멸시키는 확산과정을 역방향으로 복원하도록 학습되는 방법론인데, 지금 처음 생긴게 아니라 기존에 이미 존재하는 방법이었음.
다만 이미지 생성에서는 성능이 안좋았다고 함.
근데 이 논문에서는 저자들이 Denoising score matching 및 Langevin Dynamics에서 영감을 받아 확산모델의 학습방식을 재설계했고, 그렇게 새로운 목적함수로 훈련했더니 SOTA를 찍어버렸다고 함

그리고 확산 모델의 샘플링 과정은 auto-regressive model의 일반화인 progressive decoding의 한 형태로 해석될 수 있다고 함.

---

## 2. Background

<details markdown="1">
<summary>마르코프 체인</summary>

강화학습 MDP에서 action과 reward가 빠진 애.<br>
그냥 상태 전이확률들로만 연속되어있음

마르코프과정에서 자주 쓰이는 수식은

$$q(\mathbf{x}_{1:T}\mid \mathbf{x}_{0})=\frac{q(\mathbf{x}_{1:T},\mathbf{x}_{0})}{q(\mathbf{x}_{0})} = \frac{q(\mathbf{x}_{0:T})}{q(\mathbf{x}_{0})}$$  →  $$q(\mathbf{x}_{1:T}\mid \mathbf{x}_{0})q(\mathbf{x}_{0})=\frac{q(\mathbf{x}_{1:T},\mathbf{x}_{0})}{q(\mathbf{x}_{0})} = q(\mathbf{x}_{0:T})$$

한가지 오해하면 안되는점이, 마르코프 상태가 과거데이터는 모두 쓰레기라고 말하는게 아님!<br>
기계학습에서 베이즈 네트워크 배웠을때처럼, 미래는 현재에 직접 의존하고, 과거데이터에는 간접적으로 의존한다는 이야기임.<br>
현재 히스토리가 밝혀졌을때 이전 데이터가 더이상 쓸모없어지는거지, 이전데이터가 항상 쓸모없는게 아님.<br>
$$q(\mathbf{x}_{t}\mid \mathbf{x}_{t-1},\mathbf{x}_{0})=q(\mathbf{x}_{t} \mid \mathbf{x}_{t-1})$$은 맞지만, $$q(\mathbf{x}_{t}\mid\mathbf{x}_{0}) \neq q(\mathbf{x}_{t})$$은 아님!

</details>
    
<details markdown="1">
<summary>변분추론</summary>

알기 어려운 확률분포를 간단한 확률분포로 근사하는거.

</details>
    

Forward process는 $$q$$로 표현하고, 원본이미지 $$x_0$$에 노이즈를 점진적으로 추가해서 완전노이즈이미지 $$x_T$$를 생성하는 고정된 체인이라고 함.

결합확률 $$q(\mathbf{x}_{1},\mathbf{x}_{2}, ...,\mathbf{x}_{T}\mid \mathbf{x}_{0})$$ 를 단축해서 $$q(\mathbf{x}_{1:T}\mid \mathbf{x}_{0})$$로 쓰고, 마르코프 성질을 이용하면 

$$
\begin{align*}
q(\mathbf{x}_{1},\mathbf{x}_{2}, ...,\mathbf{x}_{T}\mid \mathbf{x}_{0})
&=q(\mathbf{x}_{1:T}\mid\mathbf{x}_0)
\\
&=q(\mathbf{x}_1\mid\mathbf{x}_0)q(\mathbf{x}_2\mid\mathbf{x}_1)q(\mathbf{x}_3\mid\mathbf{x}_2)\;...\;q(\mathbf{x}_T\mid\mathbf{x}_{T-1})
\\
&=\prod_{t=1}^T q(\mathbf{x}_{t}\mid\mathbf{x}_{t-1})
\end{align*}
$$

Reverse process는 $$p$$로 표현하고, 완전노이즈이미지 $$x_T$$에서 시작해서 이미지 $$x_0$$을 생성하는, 신경망이 학습해야할 체인이라고 함.

마찬가지로 결합확률 $$p(\mathbf{x}_{0},\mathbf{x}_{1}, ...,\mathbf{x}_{T})$$ 를 단축해서 $$p(\mathbf{x}_{0:T})$$로 쓰고, 마르코프 성질을 이용하면 

$$
\begin{align*}
p(\mathbf{x}_{0},\mathbf{x}_{1}, ...,\mathbf{x}_{T})
&=
p(\mathbf{x}_{0:T})\\
&=
p(\mathbf{x}_T)p_\theta(\mathbf{x}_{T-1}\mid\mathbf{x}_{T})p_\theta(\mathbf{x}_{T-2}\mid\mathbf{x}_{T-1})p_\theta(\mathbf{x}_{T-3}\mid\mathbf{x}_{T-2})\;...\;p_\theta(\mathbf{x}_{0}\mid\mathbf{x}_{1})
\\
&=p(\mathbf{x}_{T})\prod_{t=1}^T p_\theta(\mathbf{x}_{t-1}\mid\mathbf{x}_{t})
\end{align*}
$$

이렇게 표시할 수 있음.

순방향 과정의 전이확률 $$q(\mathbf{x}_t \mid \mathbf{x}_{t-1})$$은 가우시안 분포 $$\mathcal{N}(\mathbf{x}_t;\sqrt{1-\beta_t}\mathbf{x}_{t-1},\beta_t \mathbf{I})$$이고, 역방향 과정의 전이확률 $$p(\mathbf{x}_{t-1} \mid \mathbf{x}_{t})$$ 도 비슷하게 가우시안 분포 $$\mathcal{N}(\mathbf{x}_{t-1};\mu(\mathbf{x}_{t},t),\Sigma_\theta(\mathbf{x}_{t},t))$$임.
이때, 순방향과정은 데이터에 가우시안 노이즈를 더해 점진적으로 신호를 파괴하는 과정이므로 고정되어있지만 역방향의 전이확률은 알수 없어 스스로 학습해야함

그래서 이제 목적함수를 보면, 어쨌든 이것도 생성모델이기때문에 $$p_\theta(\mathbf{x}_{0})$$를 최대화하는 방향으로 훈련해야하는데, 그걸 구하려면 $$p_\theta(\mathbf{x}_{0})=\int p_\theta(\mathbf{x}_{0:T})d\mathbf{x}_{1:T}$$ 이렇게 주변확률분포를 계산해야되기때문에 VAE때처럼 불가능함…

$$
\begin{align*}
\mathbb{E}[-\log p_\theta(\mathbf{x_0})] 
&\leq \mathbb{E}\bigg[-\log \frac{p_\theta(\mathbf{x}_{0:T})}{q(\mathbf{x}_{1:T}\mid\mathbf{x}_0)}\bigg] 
\\
&= \mathbb{E}\bigg[-\log p(\mathbf{x}_T)-\sum_{t\geq1}\log \frac{p_\theta(\mathbf{x}_{t-1}\mid \mathbf{x}_{t})}{q(\mathbf{x}_{t}\mid\mathbf{x}_{t-1})}\bigg] =L
\end{align*}
$$

VAE에서의 ELBO처럼, 여기서도 실제 로그우도대신 대체목표를 최적화함.
대신 여기선 NLL 을 사용하기때문에, 최적화는 손실함수를 최소화하는방향으로 진행됨.

마르코프과정에서 자주 쓰이는 수식은

$$q(\mathbf{x}_{1:T}\mid \mathbf{x}_{0})=\frac{q(\mathbf{x}_{1:T},\mathbf{x}_{0})}{q(\mathbf{x}_{0})} = \frac{q(\mathbf{x}_{0:T})}{q(\mathbf{x}_{0})}$$  →  $$q(\mathbf{x}_{1:T}\mid \mathbf{x}_{0})q(\mathbf{x}_{0})=\frac{q(\mathbf{x}_{1:T},\mathbf{x}_{0})}{q(\mathbf{x}_{0})} = q(\mathbf{x}_{0:T})$$

손실함수는 KL다이버전스의 성질을 이용해서 전개함

$$
\begin{align*}
D_{KL}(q(\mathbf{x}_{1:T}\mid\mathbf{x}_{0})\parallel p_\theta(\mathbf{x}_{1:T}\mid\mathbf{x}_{0}))
&=
\mathbb{E}_q\bigg[\log \frac{q(\mathbf{x}_{1:T}\mid\mathbf{x}_0)}{p_\theta(\mathbf{x}_{1:T}\mid \mathbf{x}_{0})}\bigg] 
\\
&=\mathbb{E}_q\bigg[-\log \frac{p_\theta(\mathbf{x}_{1:T}\mid\mathbf{x}_{0})}{q(\mathbf{x}_{1:T}\mid\mathbf{x}_0)}\bigg]
\\
&=\mathbb{E}_q\bigg[-\log \frac{p_\theta(\mathbf{x}_{0:T})}{q(\mathbf{x}_{1:T}\mid\mathbf{x}_0)}+\log p_\theta(\mathbf{x}_{0}) \bigg] \geq 0
\\
\end{align*} 
$$

이기때문에

$$
\begin{align*}
\mathbb{E}[-\log p_\theta(\mathbf{x_0})] 
&\leq \mathbb{E}\bigg[-\log \frac{p_\theta(\mathbf{x}_{0:T})}{q(\mathbf{x}_{1:T}\mid\mathbf{x}_0)}\bigg] 
\\
&= \mathbb{E}\bigg[-\log p(\mathbf{x}_T)-\sum_{t\geq1}\log \frac{p_\theta(\mathbf{x}_{t-1}\mid \mathbf{x}_{t})}{q(\mathbf{x}_{t}\mid\mathbf{x}_{t-1})}\bigg] =L \tag{3}
\end{align*}
$$

이렇게 정의됨.

즉, $$L=NLL + D_{KL}(q\parallel p_\theta)$$ 꼴임!

아니 VAE의 ELBO랑 다르게 아무 철학이 없는 꼴 아님? A<B 일때 B를 줄이면 A도 줄어든다는 논리는 A랑 B의 간격이 타이트해야지 무지성 A<B라고 아무 B나 쓰면 안되는거잖아? 라고 생각했는데, 저 꼴을 보면 ELBO랑 거의 같은꼴이라는것을 알 수 있고 의문점도 해소됨.

$$
\begin{align*}
L &= \mathbb{E}_q\!\left[- \log \frac{p_\theta(\mathbf{x}_{0:T})}{q(\mathbf{x}_{1:T} \mid \mathbf{x}_0)}\right] \\ 
&= \mathbb{E}_q\!\left[- \log p(\mathbf{x}_T)- \sum_{t > 1} \log \frac{p_\theta(\mathbf{x}_{t-1} \mid \mathbf{x}_t)}{q(\mathbf{x}_t \mid \mathbf{x}_{t-1})}\right]  \\[6pt]
&= \mathbb{E}_q\!\left[- \log p(\mathbf{x}_T)- \sum_{t > 1} \log \frac{p_\theta(\mathbf{x}_{t-1} \mid \mathbf{x}_t)}{q(\mathbf{x}_t \mid \mathbf{x}_{t-1})}- \log \frac{p_\theta(\mathbf{x}_0 \mid \mathbf{x}_1)}{q(\mathbf{x}_1 \mid \mathbf{x}_0)}\right]  \\[6pt]
&= \mathbb{E}_q\!\left[- \log p(\mathbf{x}_T)- \sum_{t > 1} \log\frac{p_\theta(\mathbf{x}_{t-1} \mid \mathbf{x}_t)\,q(\mathbf{x}_{t-1} \mid \mathbf{x}_0)}{q(\mathbf{x}_{t-1} \mid \mathbf{x}_t, \mathbf{x}_0)}- \log \frac{p_\theta(\mathbf{x}_0 \mid \mathbf{x}_1)}{q(\mathbf{x}_1 \mid \mathbf{x}_0)}\right]  \\[6pt]
&= \mathbb{E}_q\!\left[- \log \frac{p(\mathbf{x}_T)}{q(\mathbf{x}_T \mid \mathbf{x}_0)}- \sum_{t > 1} \log\frac{p_\theta(\mathbf{x}_{t-1} \mid \mathbf{x}_t)}{q(\mathbf{x}_{t-1} \mid \mathbf{x}_t, \mathbf{x}_0)}- \log p_\theta(\mathbf{x}_0 \mid \mathbf{x}_1)\right]  \\[8pt]
&= \mathbb{E}_q\!\left[D_{\mathrm{KL}}\!\big(q(\mathbf{x}_T \mid \mathbf{x}_0)\,\|\,p(\mathbf{x}_T)\big)+ \sum_{t > 1} D_{\mathrm{KL}}\!\big(q(\mathbf{x}_{t-1} \mid \mathbf{x}_t, \mathbf{x}_0)\,\|\,p_\theta(\mathbf{x}_{t-1} \mid \mathbf{x}_t)\big)- \log p_\theta(\mathbf{x}_0 \mid \mathbf{x}_1)\right]
\end{align*}
$$

그리고 원래 목적함수 식 (3)을 이런식으로 변형하면, 강화학습에서 자주 했던것처럼 기대값은 그대로지만 분산은 줄어드는 효과가 있다고 함.

$$
\begin{align*}
L= \mathbb{E}_q\!\left[\underbrace{D_{\mathrm{KL}}\!\big(q(\mathbf{x}_T \mid \mathbf{x}_0)\,\|\,p(\mathbf{x}_T)\big)}_{L_T}+ \sum_{t > 1} \underbrace{D_{\mathrm{KL}}\!\big(q(\mathbf{x}_{t-1} \mid \mathbf{x}_t, \mathbf{x}_0)\,\|\,p_\theta(\mathbf{x}_{t-1} \mid \mathbf{x}_t)\big)}_{L_{t-1}}- \underbrace{\log p_\theta(\mathbf{x}_0 \mid \mathbf{x}_1)}_{L_0}\right] \tag{5}
\end{align*}
$$

그래서 효율적 학습을 위해 이 목적함수를 사용하고, 

$$
\begin{align*}
&q(\mathbf{x}_{t-1} \mid \mathbf{x}_t, \mathbf{x}_0)= \mathcal{N}\!\bigl(\mathbf{x}_{t-1};\,\tilde{\boldsymbol{\mu}}_t(\mathbf{x}_t, \mathbf{x}_0),\,\tilde{\beta}_t \mathbf{I}\bigr), \tag{6} \\[6pt]&\text{where } \tilde{\boldsymbol{\mu}}_t(\mathbf{x}_t, \mathbf{x}_0):= \frac{\sqrt{\bar{\alpha}_{t-1}}\,\beta_t}{1 - \bar{\alpha}_t}\,\mathbf{x}_0+ \frac{\sqrt{\alpha_t}\,(1 - \bar{\alpha}_{t-1})}{1 - \bar{\alpha}_t}\,\mathbf{x}_t\text{   and }\tilde{\beta}_t := \frac{1 - \bar{\alpha}_{t-1}}{1 - \bar{\alpha}_t}\,\beta_t \tag{7}
\end{align*}
$$

$$q$$도 가우시안이기때문에 이렇게 해석적으로 $$q(\mathbf{x}_{t-1} \mid \mathbf{x}_t, \mathbf{x}_0)$$을 유도할 수 있어서 몬테카를로 샘플링으로 추정할거 없이 계산이 가능하다고 함.

또, 추가적으로 순방향 연산에서의 중요한 속성 하나는 closed-form sampling이 가능하다는점임.
즉, 여러 스텝동안 $$q$$로 노이즈를 점진적으로 더할필요 없이, 한번에

$$
q(\mathbf{x}_{t}\mid \mathbf{x}_{0})=\mathcal{N} (\mathbf{x}_{t};\sqrt{ \bar{\alpha}_t}\mathbf{x}_{0},(1-\bar{\alpha}_t)\mathbf{I}) \quad \text{where } \bar{\alpha}_t=\prod_{s=1}^t \alpha_s \tag{4}
$$

이렇게 계산이 가능하다는 좋은 속성이 있음.

---

## 3. Diffusion models and denoising autoencoders

그래서 지금까지 설명한건 일반적인 Diffusion model에 관한거였다면, 이 절에서부터 DDPM에 대한 이야기가 시작됨.

기존 확산모델을 봤을때 겉보기엔 학습시킬게 별로 없는 제한적인 모델같아보이지만, 실제로는 순방향 과정의 분산 $$\beta_t$$, 역방향과정모델의 아키텍쳐, 가우시안 분포를 어떤식으로 나타낼것인지 등의 하이퍼파라미터를 정해야한다고 함

### **3.1 Forward process and $$L_T$$**

일단 저자들은 순방향 과정의 분산 $$\beta_t$$가 재 파라미터화로 학습될수있다는 사실을 무시하고 모두 상수로 고정하겠다고 함.

$$\mathbf{x}_{t}$$

### **3.2 Reverse process and $$L_{1:T-1}$$**

이제 여기서는 역방향 과정에서의 설계를 다룸.
우선 $$p_\theta(\mathbf{x}_{t-1}\mid \mathbf{x}_{t})= \mathcal{N}(\mathbf{x}_{t-1};\mu_\theta(\mathbf{x}_{t},t),\Sigma_\theta(\mathbf{x}_{t},t))$$ 이므로, 평균과 분산을 정하는 신경망을 들여다 봐야 함.

먼저 분산 설계임
$$\Sigma_\theta(\mathbf{x}_{t},t)=\sigma_t^2\mathbf{I}$$ 로 설정하고, $$\sigma_t^2 =\beta_t \text{ or }\tilde{\beta}_t=\frac{1-\bar{\alpha}_{t-1}}{1-\bar{\alpha}_t}\beta_t$$ 로 학습되지 않는 상수로 설정하는데, 저게 각각 양 극단의 선택지임에도 둘다 비슷한 성능이 나왔다고 함.
그래서 굳이 복잡하게 학습시킬필요없이 단순 상수로 고정했다고 함.

둘째로 평균인데, 여기서 핵심적인 기여가 다 나옴

논문에 맥락이 나오지 않아 좀 자세히 찾아봤는데, 식(5)에서 $$L_{t-1}$$부분이

$$
\begin{align*}
L_{t-1}=&D_{\mathrm{KL}}\!\big(q(\mathbf{x}_{t-1} \mid \mathbf{x}_t, \mathbf{x}_0)\,\|\,p_\theta(\mathbf{x}_{t-1} \mid \mathbf{x}_t)\big) 
\\
\text{where }
&q(\mathbf{x}_{t-1} \mid \mathbf{x}_t, \mathbf{x}_0)= \mathcal{N}\!\bigl(\mathbf{x}_{t-1};\,\tilde{\boldsymbol{\mu}}_t(\mathbf{x}_t, \mathbf{x}_0),\,\tilde{\beta}_t \mathbf{I}\bigr), \\
&p_\theta(\mathbf{x}_{t-1}\mid \mathbf{x}_{t})= \mathcal{N}(\mathbf{x}_{t-1};\mu_\theta(\mathbf{x}_{t},t),\sigma_t^2\mathbf{I})
\end{align*}
$$

이므로, 손실함수는 $$D_{KL}(\mathcal{N}_1\parallel\mathcal{N}_2)$$ 꼴이 되고, 이 정규분포간의 KL다이버전스는

$$
D_{KL}(\mathcal{N}_1 \parallel \mathcal{N}_2) = \frac{1}{2} \left( \log \frac{|\Sigma_2|}{|\Sigma_1|} - d + \text{tr}(\Sigma_2^{-1} \Sigma_1) + (\mu_2 - \mu_1)^T \Sigma_2^{-1} (\mu_2 - \mu_1) \right)
$$

이런 공식이 존재한다고 함.

이걸 계산하면

$$
\begin{align*}
L_{t-1} &= \mathbb{E}_q[D_{KL}(q\parallel p_\theta)]
\\
&= \mathbb{E}_q[D_{KL}(\mathcal{N}_1 \parallel \mathcal{N}_2)]
\\
&=\mathbb{E}_q[D_{KL}(q \parallel p_\theta)]
\\
 &= \mathbb{E}_q\Bigg[\underbrace{\frac{1}{2\sigma_t^2} ||\tilde{\mu}_t - \mu_\theta||^2}_{\text{1. 평균(mean)에 대한 항}} + \underbrace{\frac{1}{2} \left( d \log \frac{\sigma_t^2}{\tilde{\beta}_t} + d \frac{\tilde{\beta}_t}{\sigma_t^2} - d \right)}_{\text{2. 분산(variance)에 대한 항}}\Bigg]
\\
&=\mathbb{E}_q\!\left[\frac{1}{2\sigma_t^2}\left\lVert\tilde{\boldsymbol{\mu}}_t(\mathbf{x}_t, \mathbf{x}_0)- \boldsymbol{\mu}_\theta(\mathbf{x}_t, t)\right\rVert^2\right] + C \tag{8}
\end{align*}
$$

이런식으로 정리됨.

근데 식 (4)를 보다보면, $$\mathbf{x}_{t}(\mathbf{x}_{0},\epsilon)=\sqrt{\bar{\alpha}_t}\mathbf{x}_{0}+\sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}$$ 로 재파라미터화 할 수 있다는것을 알 수 있고, 

이걸 식 (7)에 적용해보면 

$$
\begin{align*}
L_{t-1} - C
&= \mathbb{E}_{\mathbf{x}_0, \boldsymbol{\epsilon}}\!\left[\frac{1}{2\sigma_t^2}\left\lVert\tilde{\boldsymbol{\mu}}_t\!\left(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon}),\frac{1}{\sqrt{\bar{\alpha}_t}}\bigl(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon}) - \sqrt{1 - \bar{\alpha}_t}\,\boldsymbol{\epsilon}\bigr)\right)- \boldsymbol{\mu}_\theta\!\bigl(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon}), t\bigr)\right\rVert^2\right]  \\[6pt]
&= \mathbb{E}_{\mathbf{x}_0, \boldsymbol{\epsilon}}\!\left[\frac{1}{2\sigma_t^2}\left\lVert\frac{1}{\sqrt{\alpha_t}}\!\left(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon})- \frac{\beta_t}{\sqrt{1 - \bar{\alpha}_t}}\,\boldsymbol{\epsilon}\right)- \boldsymbol{\mu}_\theta\!\bigl(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon}), t\bigr)\right\rVert^2\right] \tag{10}
\end{align*}
$$

이고, 결국 $$\boldsymbol\mu_\theta$$는

$$
\boldsymbol{\mu}_\theta\!\bigl(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon}), t\bigr) \approx \frac{1}{\sqrt{\alpha_t}}\bigg( \mathbf{x}_{t}-\frac{\beta_t}{\sqrt{1-\bar{\alpha}_t}}\boldsymbol{\epsilon }\bigg)
$$

이렇게 예측하도록 되도록 신경망을 훈련해야함.

근데 지금은 역방향과정이므로 $$\mathbf{x}_t$$는 known이고 $$t$$도 주어지므로, $$\boldsymbol{\epsilon}$$만 예측하면 됨
그래서 $$\mu_\theta$$ 전체를 신경망으로 모사하는 대신 $$\boldsymbol{\epsilon}_\theta$$만 신경망으로 모사하면 됨.

이때, 무작위성을 학습한다는게 아니라 이미 추가된 무작위성을 $$\mathbf{x}_{t},t$$를 보고 예측하라는거임.
패턴이 없는 순수 무작위를 학습한다는건 말이 안됨.
여기서 하라는건, 무작위성을 학습하라는게 아니라, 이미지 원본을 많이 봤으면 진짜 이미지 $$\mathbf{x}_{0}$$의 패턴을 알테니 $$\mathbf{x}_{t}$$가 주어지면 $$\mathbf{x}_{t}=\mathbf{x}_{0}+\boldsymbol{\epsilon}$$ 므로 노이즈가 뭔지 골라내라는거임.
입력이 들어왔을때 자기가 아는 패턴을 제외한 나머지를 출력하도록 훈련되는 이런 아이디어를 잔차학습이라고 한다고 하고, 노이즈 $$\boldsymbol{\epsilon}$$을 예측하라는부분은 사실상 실제로는 $$\mathbf{x}_{0}$$를 예측하라는 의미인거임.
결론적으로는, 형식적으로는 출력되는 나머지가 랜덤부분이지만 실제 학습하는 알맹이는 알고있는 패턴부분이기때문에 말이 되는거임.

$$
\boldsymbol{\mu}_\theta\!\bigl(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon}), t\bigr) 
=
 \frac{1}{\sqrt{\alpha_t}}\bigg( \mathbf{x}_{t}-\frac{\beta_t}{\sqrt{1-\bar{\alpha}_t}}\boldsymbol{\epsilon }_\theta(\mathbf{x}_{t},t)\bigg) \tag{11}
$$

그러므로 $$\boldsymbol{\mu}_\theta$$는 이렇게 파라미터화 될 수 있음 (일단 이정도로만 넘어가자…)

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>🎯</div>
<div markdown="1" style="flex:1; min-width:0;">

**잔차학습**<br>
랜덤한 소음이 들리는 공사장속에서, 스피커로 모차르트 14번 소나타를 틀어놓는중임.<br>
이때 공사장소음만 분류해보라고 하면, 원래 아무 입력도 없는상태에선 랜덤을 예측할수가 없음.<br>
근데 완전 무에서 예측하라는게 아니라 합쳐진 음성이 주어짐.<br>
근데 나는 모차르트 14번 소나타를 학습하는중이라 어느정도 멜로디를 알고있음.<br>
그렇게되면 합쳐진 음성에서 소나타를 빼고 랜덤소음을 추출해낼수 있는데, 겉보기엔 랜덤성을 예측하는 말도안되는 상황같지만 사실은 랜덤소음외의 나머지부분을 잘 학습함으로서 분류해내는거임

</div>
</div>

$$
\mathbf{x}_{t-1}= \frac{1}{\sqrt{\alpha_t}}\left(\mathbf{x}_t- \frac{\beta_t}{\sqrt{1 - \bar{\alpha}_t}}\,\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)\right)+ \sigma_t \mathbf{z}, \quad \mathbf{z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I}) \tag{LD}
$$

그래서 아까랑 비슷하게, 결과적으로 $$\mathbf{x}_{t-1}$$은 이렇게 표현됨.

이제 식 (10)에 (11)을 대입해보면, 

$$
\begin{align*}
&\mathbb{E}_{\mathbf{x}_0, \boldsymbol{\epsilon}}\!\left[\frac{1}{2\sigma_t^2}\left\lVert\frac{1}{\sqrt{\alpha_t}}\!\left(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon})- \frac{\beta_t}{\sqrt{1 - \bar{\alpha}_t}}\,\boldsymbol{\epsilon}\right)- \boldsymbol{\mu}_\theta\!\bigl(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon}), t\bigr)\right\rVert^2\right]
\\
&=\mathbb{E}_{\mathbf{x}_0, \boldsymbol{\epsilon}}\!\left[\frac{1}{2\sigma_t^2}\left\lVert\frac{1}{\sqrt{\alpha_t}}\!\left(\mathbf{x}_t(\mathbf{x}_0, \boldsymbol{\epsilon})- \frac{\beta_t}{\sqrt{1 - \bar{\alpha}_t}}\,\boldsymbol{\epsilon}\right)- \frac{1}{\sqrt{\alpha_t}}\bigg( \mathbf{x}_{t}-\frac{\beta_t}{\sqrt{1-\bar{\alpha}_t}}\boldsymbol{\epsilon }_\theta(\mathbf{x}_{t},t)\bigg) \right\rVert^2\right] 
\\
&=\mathbb{E}_{\mathbf{x}_0, \boldsymbol{\epsilon}}\!\left[\frac{\beta_t^2}{2\sigma_t^2\alpha_t(1-\bar{\alpha}_t)}\left\lVert \boldsymbol{\epsilon}-\boldsymbol{\epsilon}_\theta(\mathbf{x}_t,t)\right\rVert^2\right]
\\
&= \mathbb{E}_{\mathbf{x}_0, \boldsymbol{\epsilon}}\!\left[\frac{\beta_t^2}{2\sigma_t^2\alpha_t(1-\bar{\alpha}_t)}\left\lVert \boldsymbol{\epsilon}-\boldsymbol{\epsilon}_\theta(\sqrt{\bar{\alpha}_t}\mathbf{x}_{0}+\sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon},t)\right\rVert^2\right] \tag{12}\end{align*}
$$

인데, 이건 denoising score matching이랑 비슷하다고 함

![DDPM의 방향 그래프 모델: 노이즈 x_T에서 이미지 x_0로 가는 역방향 과정과 순방향 과정 q](/assets/img/ai_paper_reviews/Diffusion/diffusion-fig1.png)

![DDPM의 학습(Algorithm 1)과 샘플링(Algorithm 2) 알고리즘](/assets/img/ai_paper_reviews/Diffusion/diffusion-fig2.png)

알고리즘은 이렇게 생겼음

**Sampling :**

먼저 샘플링과정(훈련한 모델 추론돌리는 과정)부터 보면, 이건 순수 노이즈에서 시작해 디노이징과정을 반복해서 최종 이미지를 만들어내는 과정임

아까 구한 식 (LD)를 보면, 이게 Langevin dynamics랑 비슷한 꼴이라고 함.
랑주뱅 역학은 입자가 움직이는 과정을 결정론적과 확률적 힘으로 나눠서 모델링하는 틀인데, 중력,탄성력, 점성등의 고전역학적 힘을 결정론적 힘으로 분류하고 미시적 힘은 통계적인 확률적힘으로 분류함.

결정론적힘은 Drift라고 부르고, DDPM에서는 노이즈 제거항 $$\boldsymbol{\epsilon}_\theta$$이 여기에 해당됨.
학습의 데이터분포 경사역할을 한다고 함.

확률적 힘은 Diffusion이라고부르고, 무작위 노이즈항 $$\sigma_t\mathbf{z}$$가 여기에 해당함.
입자가 무작위로 흔들리게 해서 한곳에 갇히는것을 방지하고 탐색을 돕는 역할이라고 함.

그래서 DDPM의 샘플링과정을 랑주뱅동역학의 시각으로 해석하면, 노이즈 $$\mathbf{x}_{T}$$에서 이미지 $$\mathbf{x}_{0}$$쪽으로 디 노이징을 하면서 꾸준히 나아가는데, 경로의 다양성을 위해 약간의 무작위요소를 추가하는 과정이라고 볼 수 있음.

**Training :**

이제 훈련과정을 보면, 먼저 원본이미지 훈련데이터셋에서 원본이미지를 하나 무작위로 뽑고, 특정 시간 t를 무작위(uniform) 선택함.
이후 실제 $$\boldsymbol{\epsilon}$$는 가우시안분포에서 무작위로 뽑고, simple Loss (식 12)를 구하기위해 $$\boldsymbol{\epsilon}_\theta$$를 알아야하므로 순방향 closed form 식(4)로 $$\mathbf{x}_{t}$$를 계산한 후 Loss를 계산함.
이후 경사하강법으로 신경망 $$\theta$$ 업데이트. 

스코어함수라는게 있는데, $$s(\mathbf{x})=\nabla_{\mathbf{x}}\log p(\mathbf{x})$$ 꼴임.
생성모델 MLE 최적화할때 쓰는 그라디언트랑은 다름.
$$\nabla_\theta\log p_\theta(\mathbf{x})$$은 모델을 변경시키면서 데이터의 확률을 높이는거고, 스코어함수는 데이터 자체를 변경하면서 고밀도 데이터분포영역으로 이동하는거임.
근데 Denoising Score Matching(DSM)이라는 방법에 따르면, 이 스코어함수를 학습하는건 노이즈가 섞인 데이터에서 노이즈를 제거하는 디 노이징과정을 학습하는것과 동치라는것이 증명되었고, 따라서 $$\lVert \epsilon - \epsilon_\theta \rVert$$ 를 훈련시키는 방식으로 스코어함수를 훈련한다고 함.

우리가 역방향에서 하는일이 $$\mathbf{x}_{T} \rightarrow\mathbf{x}_{0}$$ 으로 가면서 점점 로그확률 $$\log p(\mathbf{x}_{t})$$를 올리는쪽으로 변형시키는건데, 이게 결국 score function이라는 나침반을 보면서 하는 과정이고, 이걸 잔차학습을 통해 해도 된다는게 DSM의 주요내용.

요약하면, 역과정 함수 $$\boldsymbol{\mu_\theta}$$를 $$\boldsymbol{\tilde{\mu_t}}$$
를 예측하도록 훈련할수도 있고, 파라미터화를 수정해서 $$\boldsymbol{\epsilon}$$을 예측하도록 훈련할수도 있고, 바로 $$\mathbf{x}_0$$를 예측하도록 할수도 있지만 $$\boldsymbol{\epsilon}$$을 예측하는게 가장 효과적이었다고 함.
또한, 그렇게 하면 샘플링과정에서는 다음 이미지가 랑주뱅 동역학의 식과 비슷한 형태가 나오고, 훈련과정에서는 목적함수가 DSM에서와 유사한 목적함수로 단순화되는것을 발견했다고 함.
