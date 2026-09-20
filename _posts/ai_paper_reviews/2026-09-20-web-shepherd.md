---
title: WEB-SHEPHERD 리뷰
date: 2026-09-20 00:50:00 +0900
categories: [AI Paper Reviews, Agents]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**WEB-SHEPHERD: Advancing PRMs for Reinforcing Web Agents**<br>
Date: 2025.5.21<br>
Venue: NeurIPS 2025 Spotlight<br>
Notable author: Hyungjoo Chae et al (Lang AGI + DLI lab)<br>
Comprehension: 3단계 

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>💡</div>
<div markdown="1" style="flex:1; min-width:0;">

**Motivation**<br>
Web navigation task에서, long-horizon 작업을 하려면 PRM을 통해 탐색을 하는것이 필수적인데, 지금까지는 Web navigation 맞춤 PRM이 없어 범용 MLLM을 PRM으로 사용.<br>
근데 엄청나게 비효율적이고 성능도 나빠서, WEB-SHEPHERD라는 Web navigation 맞춤 PRM을 만듦. 그리고 덤으로 PRM을 만들때 쓴 WEBPRM COLLECTION과 평가 벤치마크인 WEBREWARDBENCH도 공개.<br>
**느낀점**<br>
기존의 PRM이 개떡같은 보상신호를 주던 문제를 해결한다는점은 처음 예상과 같았음.<br>
근데 첫 예상과 달리 기존 PRM에 들어가는 비대한 입력 컨텍스트를 해소해서 비용을 확 줄이는건 아니었음.<br>
비용이 줄어든건 Qwen3B, 8B같은 소형모델로 전환되었기때문에 그랬던거였음…

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>💡</div>
<div markdown="1" style="flex:1; min-width:0;">

**WebPRM흐름**<br>
먼저, task $$I$$에 대한 인간의 Demonstration $$A^+$$과 obervation $$O$$를 수집하고, GPT-4o에 넣어서 체크리스트 $$C$$ 생성.<br>
rejected action $$A^-$$도 만드는데, 다양한 LLM을 통해 오답을 생성하고 규칙기반으로 확실히 필터링.<br>
이후 GPT-4o에 넣어서 각 행동에 대한 자연어피드백 $$F$$와 판단 토큰 $$J$$ 생성.<br>
그렇게 완성된 데이터는 $$\mathcal{D}=(I,O,C,A^+,A^-,F,J)$$<br>
**WEB-SHEPHERD 학습흐름**<br>
먼저, 체크리스트 생성하게 $$\mathcal{L}=-\sum\log P(C\mid I)$$ 이런식으로 SFT 진행.<br>
이후  $$\mathcal{L}_{NTP}=-\sum_t \log P_\theta(y_t \mid y_{<t},I,C,o,a)$$ 이렇게 자연어피드백과 판단을 이어서 생성하도록 SFT.<br>
**WEB-SHEPHERD 추론흐름**<br>
task $$I$$를 받아 체크리스트 $$C$$ 부터 만들고, $$(I,C,o,a)$$를 받아 피드백과 판단을 생성한 후 보상 반환

</div>
</div>

## 0. Abstract

이 논문은 웹 내비게이션 전용보상모델인 Web-sheperd를 제안하는 연구임.
기존의 연구에서는 가치함수모델(보상모델이랑 그냥 섞어쓰는듯)을 그냥 MLLM에 적당히 정보 넣어주고 프롬프팅해서 알아서 채점해달라고 하거나 아니면 단계별 상태를 그냥 사람이 직관적으로 라벨링한걸 fine-tuning시키는 등 점수 대~충 나오게 엔지니어링해서 썼었는데, 상당히 문제가 많았었음.
Tree search agent 읽을때도 엄청나게 비효율적이고 컨텍스트 잡아먹는 괴물같았고, WMA에서도 너무 대충 만들어서 이게 과연 제대로된 보상신호를 주는 PRM일까? 하는 의문이 있었는데, 얘는 4만개의 단계별 preference pair를 갖고 제대로 만들어진 web navigation 전용 PRM이라 기존 방법론들의 가려운 등을 제대로 긁어주는듯.
이걸 사용한 agent들은 성능은 훨씬 오르고, 비용은 무려 1/10 수준으로 떨어지는 경이로운 성능을 보였다고 함.
그래서 이름도 agent를 올바로 이끌어준다는 뜻의 shepherd(양치기) 인듯.

---

## 1. Introduction

웹 agent를 만들때 간단한 작업은 어느정도 할 수 있게 되었지만 장기적인 long-horizon task에서는 여전히 불안정하고 성능이 떨어짐.
다른 분야에서는 맞춤 보상모델을 통해 test-time탐색을 하거나 강화학습을 하거나 해서 많은 발전이 있었는데,  web navigation 분야에서는 이런 맞춤 보상모델이 없어서 MLLM을 쓰거나 했음.
근데 Tree search agent는 GPT-4o를 이용해 탐색을 하면 2000만원이 들고, 성능도 좋지 않다고 함.

그래서 자기들은 web navigation의 trajectory를 평가하는 맞춤 보상모델인 WEB-SHEPHERD를 만들었고, ORM이 아니라 PRM이라고 함.
ORM으로 만들면 에피소드가 끝난다음에 에피소드에 대한 평가를 하게되는데, 웹에서는 실제 실행을 해버리기때문에 잘못된 행동을 하기 전에 막아야해서 스텝별 피드백을 줄 수 있는 PRM으로 만듦.
long-horizon task에서 agent를 제대로 안내할 수 있는 스마트한 PRM을 만들기 위해 사용자의 고수준 목표를 명확한 하위목표로 분해하는 체크리스트를 사용한다고 함.

WEB-SHEPHERD라는 최초의 web navigation 전용 PRM을 만든것도 대단하지만, PRM을 만들기위한 WEBPRM COLLECTION이라는 데이터셋과, PRM을 평가할 수 있는 WEBREWARDBENCH를 만들고 공개한게 정말 큰 기여라고 함.
그리고 이 벤치마크에서 PRM을 평가했을때 GPT-4o-mini은 5점이었지만 WEB-SHEPHERD는 85점으로 압살을 해버렸다고 함.

---

## 2. Related work

MLLM같은 agent만으로는 환경이 바뀌거나 horizon이 길어지면 실패하는경우가 많아서, 피드백을 받을 수 있는 test-time scaling이나 RL같은 방법을 파는게 요즘 메타가 됐다고 함.
그 피드백을 구현하기 위해서 ORM이나 PRM같은 모델을 연구하는데, 범용 MLLM을 프롬프팅해서 PRM으로 썼을때 별로라서 제대로된 PRM을 만듦.

---

## 3. Preliminaries

<figure style="width:50%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig1.png" alt="논문 Figure 2: POMDP로 본 웹 네비게이션 예시 - User Instruction, 스크린샷과 접근성 트리로 된 Observation, Action" style="width:100%;">
</figure>

웹 네비게이션은 $$(\mathcal{S},\mathcal{A},\mathcal{O},T,R)$$이렇게 부분관측만 가능한 POMDP로 정의됨.
상태전이확률을 $$T(s'\mid s,a)$$로 정의함.
관측 $$o_t \in \mathcal{O}$$는 $$o_t = \{o_t^{txt},o_t^{img}\}$$ 이렇게 접근성트리와 이미지 2가지 요소로 이루어짐.

---

## 4. WebPRM collection

![논문 Figure 3: WebPRM Collection 데이터셋 수집 과정 개요(위)와 데이터 인스턴스 예시(아래: Instruction, Checklist, Chosen/Rejected Action, Feedback & Judgement)](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig2.png)

만드는 데이터셋의 형식은 $$\mathcal{D}=(I,O,C,A^+,A^-)$$ 이고, $$C$$는 후술할 체크리스트임. 
$$O,A^+$$는 Demonstration에서 나온 trajectory $$O=(o_1,o_2,...,o_n),A^+=(a_1^+,a_2^+,...,a_n^+)$$ 이고, 
$$A^-$$는 실패한 행동들 $$A^-=(a_{1,i}^+,a_{2,i}^+,...,a_{n,i}^+)$$ 임.
실패한 행동은 다양한 모델들을 이용해서 만들어낸다고 함.

### 4.1 Collecting user instruction and expert trajectory

우선 모범데이터를 얻기위해 Mind2Web이 사용했던 웹사이트들에서 인간의 Demonstration을 수행함.
Playwright라는 프레임워크를 이용해서 사람의 Demonstration trajectory 를 `click('id=123')` 이런식으로 기록해줬음.

### 4.2 Annotating checklist and rejected action

고수준 목표를 세분화한 체크리스트를 만들때도 너무 low level에서 만들면 의미론적으로 맞는데 다르다고 판단하는 일이 발생할 수 있어서 각 단계를 덜 granullar하게 추상적으로 만듦.
체크리스트 $$C$$는 사용자지시 $$I$$와 Demonstration $$A^+$$를 GPT-4o에 넣어서 만들어내도록 함.

그리고 PRM을 만들때 잘못된 행동도 같이 보여줘야 좋은 모델이 나오기때문에 rejected actions들도 만들어냄.
Qwen-2.5-VL-7B, Qwen-2.5-VL-72B, GPT-4o-mini, Demonstration으로 fine-tuning된 Qwen-2.5-3B모델 등 다양한 모델을 써서 행동을 샘플링하는데, 먼저 Demonstration과 다른 행동을 오답후보로 등록함.
근데 기능적으로는 정답일수도 있으므로 드래그를 해야되는데 클릭을 한다던지 하는 확실한 오답을 규칙기반으로 추출해서 최종적으로 5개의 rejected actions를 얻어냄.

### 4.3 Dataset statistics

<figure style="width:43%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig3.png" alt="논문 Figure 4: WebPRM Collection 통계 - instruction과 웹사이트 분포, 난이도별 trajectory 길이와 체크리스트 수" style="width:100%;">
</figure>

$$I$$를 다양한 웹사이트 다양한 난이도에 대해 주석자들이 직접 만들게 시켰었는데, 검증해보니 실제로 다양한 웹사이트에서 만들었고 난이도도 쉬움은 3~4개의 체크리스트 항목을 포함하면서 짧은 step만에 완수될수 있는 지시인 반면 중간과 어려움은 4~5개의 체크리스트 항목을 포함하면서 step은 훨씬 길게 요구되는 문제였다고 함.
주석자들이 만든 지시가 충분히 신뢰할 수 있다는 밑밥 까는거임.

### 누락된 부분(4.4?)

<figure style="width:61%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig4.png" alt="논문 Figure 20: baseline 모델이 체크리스트로 보상을 매길 때 쓴 프롬프트 전문" style="width:100%;">
</figure>

가장 중요한 $$F,J$$ 라벨을 생성하는 부분이 설명이 안되어있음
GPT-4o에 $$I,O,C,a$$를 넣고 $$F,J$$를 출력하게 하는데, 이게 보상점수 매기고 하는 제일 중요한 부분인데 왜인지 모르게 안적어놨음.
그래서 위의 데이터셋 정의 $$\mathcal{D}=(I,O,C,A^+,A^-)$$는 틀린거고, $$\mathcal{D}=(I,O,C,A^+,A^-,F,J)$$로 쓰는게 맞음!

---

## 5. WEB-SHEPHERD

![논문 Figure 5: WEB-SHEPHERD 개요(왼쪽: checklist generation과 rewarding with checklist)와 활용 사례(오른쪽: reward-guided search, refine, RL)](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig5.png)

### 5.1 step 1: checklist generation

먼저, 사용자 지시 $$I$$가 주어지면 자연어문장 $$k$$개로 이루어진 체크리스트 $$C=(g_1,g_2,...,g_k)$$를 만듦.

훈련할때는 아까 데이터셋에서 GPT-4o로 만들어놓은 $$C$$를 출력하도록 $$\mathcal{L}=-\sum\log P(C\mid I)$$ 이런식으로 훈련할거임(논문에는 안나와있음).

이게 상당히 혼란스러운데, 아마 훈련때는 체크리스트 $$C$$에 진짜 체크리스트만 있는게 아니라 논리적 분석이 있었을 가능성이 큼.
GPT-4o한테 $$I,A^+$$을 같이 줘서 문제푸는 단계를 분석하게 하고 그 다음에 체크리스트를 출력하는거임.
이걸 WEB-SHEPHERD 한테 Distill할때는 그래서 저 분석과정까지 학습시키고, 추론때는 먼저 짧게 문제분석하게 한다음에 체크리스트 $$C$$를 출력하게 하는거같음.

![논문 Figure 21: WEB-SHEPHERD가 체크리스트를 생성할 때 쓰는 프롬프트](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig6.png)

### 5.2 step 2: reward modeling with checklist

<figure style="width:79%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig7.png" alt="논문 Figure 22: WEB-SHEPHERD가 보상을 매길 때 쓰는 프롬프트 전문" style="width:100%;">
</figure>

그 다음 MLLM은 지시 $$I$$, 체크리스트 $$C$$, 관측 $$o$$와 행동 $$a$$를 입력받아 피드백 $$F$$와 판정 $$J$$를 생성해냄.
재밌게도 PRM에서 바로 점수를 출력하는 로직이 아니라 자연어 생성을 한 다음에 점수로 변환함.

훈련할때는, 피드백과 판정을 이어서 $$y=[F;J]$$ 이렇게 쭉 생성할거기때문에, 손실함수도 

$$
\mathcal{L}_{NTP}=-\sum_t \log P_\theta(y_t \mid y_{<t},C,o,a)
$$

요런식으로 정의하고 fine-tuning함.
$$J$$는 Yes / No / In Progress가 출력되도록 하는데, 이걸 이용해서 점수로 변환할거고 Done이나 Correct같은 유의어도 인정해준다고 함.

먼저 $$F\sim P(\cdot \mid I,C,o,a)$$ 이렇게 자연어 피드백을 출력하는 이유는 판단을 내리기 전 수행하는 일종의 CoT역할을 해주기 때문임.

이제 모든 준비가 끝났으면 판단 $$J$$를 생성하는데, 이때 토큰들의 생성확률을 이용해서 보상점수로 매핑함.

$$
r_k(o,a)=\frac{1}{L}\sum_l^L P(\text{"Yes"}\mid I,C,o,a,F)+0.5\times P(\text{"In Progress"} \mid I,C,o,a,F)
$$

논문에는 설명이 안나와있지만 $$L$$은 샘플링해서 평균을 내는 일종의 self-consistency 횟수라고 함.
$$L$$을 체크리스트 수라고 했는데 오타같음.

---

## 6. Experiments

이제 자기들 PRM이 잘 만들어졌는지, PRM이 좋아졌을때 web agent 시스템성능이 개선되는지 실험함 .

### 6.1 WEBREWARDBENCH

**6.1.1 Setup**

근데 web navigation PRM 벤치마크가 존재하지 않았어서 저자들이 WEBREWARDBENCH라는 벤치마크부터 먼저 만든다고 함.

일단 벤치마크에 Demonstration 데이터는 Mind2Web에서 707개, WebArena에서 69개 가져왔음.
Mind2Web은 정적 벤치마크라서 이미 사용자 trajectory가 있었는데, WebArena는 그냥 시뮬레이터라서 직접 자기들이 거기서 활동하면서 만들었다고 함.

데이터는 $$(o_t, a_t^+, \{a_{(t,i)}^-\}_{i=1}^4)$$ 이렇게 각 관측마다 정답 1개와 오답 4개로 구성함.
관측이랑 정답행동은 Demonstration에서 가져오고, 오답은 WEB-SHEPHERD에서 처럼 다른 모델들돌리고 규칙기반 필터링하는식으로 만듦.

평가 메트릭은 MRR(평균역순위), Acc. step(단계별 정확도), Acc. traj(궤적 정확도)를 사용함.
5스텝짜리 traj에서 정답행동을 1등→1등→3등→2등→1등 으로 예측했다면,

$$
\begin{align*}
&\text{MRR}:\frac{1}{1}+\frac{1}{1}+\frac{1}{3}+\frac{1}{2}+\frac{1}{1}=3.8333...  \\
&\text{Acc. step}: \frac{3}{5}=0.6\\
&\text{Acc. traj}: \frac{0}{1}=0\\
\end{align*}
$$

이렇게 계산됨.

PRM모델 베이스라인 경쟁자들로는 GPT-4o-mini, GPT-4o와 Qwen-2.5-VL-72B 이렇게 오픈모델과 클로즈모델 둘다 씀.

그리고 WEB-SHEPHERD의 베이스모델로는, 텍스트환경에서 Qwen-2.5-3B, Qwen-3-8B, 멀티모달환경에서 Qwen-2.5-VL-3B를 사용해서 LORA로 fine-tuning했다고 함.

**6.1.2 Results**

![논문 Table 1: WebRewardBench 평가 결과 - GPT-4o-mini, GPT-4o, Qwen-2.5-VL-72B와 WEB-SHEPHERD(3B, 8B)의 MRR과 Acc.(traj)](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig8.png)

이제 여기부터 본게임인데, 그렇게 만든 벤치마크에서 기존 베이스라인과 WEB-SHEPHERD를 실험해봄.

결과가 상당히 통쾌한데, 먼저 MLLM을 PRM으로 썼을때 베이스라인들은 Acc. traj에서 점수가 한자릿수로 개판이 난데에 비해 WEB-SHEPHERD는 50%로 학살을 해버림.

체크리스트 효과도 실험했는데, 체크리스트를 썼을때 유의미하게 성능이 더 잘나왔음.

좀 놀라웠던건 멀티모달을 사용했을때 그냥 텍스트로 DOM 받았을때보다 성능이 오히려 낮아지는 경향이 있었다는거임.
기존의 web navigation분야가 텍스트에서 멀티모달로 진화하는 흐름이라고 했는데, 기존연구들이 사기를 친건 아닌지 의심되는 부분…
저자들은 멀티모달의 이미지가 텍스트정보를 오히려 방해하는 방향으로 작용했다고 봤음.

### 6.2 Reward-guided trajectory search

![논문 Table 2: WebArena-lite에서 GPT-4o-mini와 GPT-4o를 정책으로 쓴 trajectory search의 PRM별 성공률](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig9.png)

여기가 궁극적인 실험대임.
그래서 PRM을 개선했을때 web agent의 성능이 실제로 향상되는지? 향상된다면 얼마정도인지 실험.
그리고 PRM을 사용할때는 best-of-N 방식으로 탐색을 진행
실험결과, 뛰어난 PRM(WEB-SHEPHERD)를 사용하니까 agent의 성능이 확 올라가는것을 확인했음!!

추가적으로, 완전 OOD인 WorkArena에서 WEB-SHEPHERD를 사용해서 탐색하는 실험과 self-refine(reflexion이랑 다름)을 해봤는데 

![논문 Table 3: WorkArena에서 GPT-4o-mini를 정책으로 쓴 trajectory search의 PRM별 성공률](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig10.png)

먼저 WorkArena의 결과를 보면 OOD인 환경에서도 훌륭한 PRM을 썼을때 성능이 확 뛰는것을 확인함!

<figure style="width:44%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig11.png" alt="논문 Table 4: WebArena-lite에서 WEB-SHEPHERD 피드백으로 refinement했을 때의 성공률" style="width:100%;">
</figure>

그리고 self-refine에서 PRM을 WEB SHEPHERD를 사용했을때도 성능향상을 확인함.

---

## 7. Discussion

### 7.1 The impact of checklist quality in reward prediction

![논문 Figure 7: 체크리스트 품질 평가(왼쪽)와 체크리스트 품질에 따른 보상 정확도(오른쪽)](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig12.png)

체크리스트의 품질이 얼마나 중요한지 실험해봄.
어쨌든 WEB-SHEPHERD도 대형모델을 Distill해서 체크리스트를 생성하기때문에 체크리스트의 품질에 대한 걱정이 있었는데, LLM이 체크리스트의 품질을 정성평가해주는 LLM-as-Judge 벤치마크 G-Eval로 채점해봤을때 WEB-SHEPHERD의 점수가 괜찮게 나왔음.

원래 초기버전의 WEB-SHEPHERD는 GPT-4o로 체크리스트 라벨 $$C$$를 만들때 $$I,A^+$$만 넣어서 바로 만들도록 한걸 썼는데, 그렇게 하니까 체크리스트 품질이 2.97점으로 처참하게 박살이 났었음.
그래서 이후에는 분석과정을 GPT-4o가 만들고, WEB-SHEPHERD도 Distill 받을때 그 분석과정까지 훈련받은 뒤 생성할때도 $$I$$에 대한 간단한 분석을 수행한 수 checklist를 생성하게 바뀜.

어쨌든 그렇게 좋은 품질의 체크리스트부터 좋은품질의 체크리스트까지 실험해봤을때, agent의 성능에 확실히 영향을 주는것을 확인.

### 7.2 Training objective: Bradley-terry modeling vs generative reward modeling

<figure style="width:52%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig13.png" alt="논문 Figure 8: 학습 목적함수 분석 - Bradley-Terry modeling과 WEB-SHEPHERD의 Mind2Web, WebArena 성능 비교" style="width:100%;">
</figure>

자기들이 BT모델로 선호도 보상을 주지 않고 특이하게 생성형으로 보상모델을 만든것에 대한 비교를 진행했는데, 훈련데이터와 OOD인 WebArena에서도 WEB-SHEPHERD의 성능은 강건하게 유지된 반면 BT모델은 성능이 뚝 떨어진걸 보이면서 BT모델은 체크리스트를 잘 사용하지 못해서 그런것이라고 판단함.
근데 정성분석을 해보지도 않고 저렇게 바로 체크리스트를 못쓴다고 판단하는건 성급한거 아닌가 싶긴 함…

### 7.3 Cost efficiency of WEB-SHEPHERD

![논문 Figure 1: WEB-SHEPHERD(3B)의 성능과 비용 효율 - 기존 baseline 대비 높은 성능과 훨씬 낮은 비용](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig14.png)

이게 가장 킥인것같은데, 성능은 압도적이면서도 GPT-4o-mini를 PRM으로 썼을때보다 10배, GPT-4o를 썼을때보다 100배가 저렴함…
fig22에서 reward 생성할때 들어가는 입력의 크기는 기존의 범용 PRM들과 비교했을때 크게 다르지 않은것같지만, 모델이 작기때문에 이런 비용차이가 발생하는듯

### 7.4 Data scaling law for PRM training

![논문 Table 5: (a) instruction 비율, (b) rejected action 최대 개수가 모델 성능에 미치는 영향](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig15.png)

데이터 수, rejection 된 행동을 줄어보는 실험을 진행했는데, 데이터수가 줄어들면 성능이 크게 떨어짐.
그리고 재밌는건 rejection 행동을 4개 말고 3개로만 줄여도 성능이 급락했다는거임.
60점에서 20점이 돼버렸는데, Acc. traj이라 더 극단적인 점수차가 벌어진것같지만 어쨌든 오답을 많이 확보하는것이 매우 중요함을 알 수 있음.

### 7.5 Case study

![논문 Figure 9: reward-guided trajectory search의 성공·실패 사례에서 보상 점수 추세](/assets/img/ai_paper_reviews/WEB-SHEPHERD/web-shepherd-fig16.png)

성공사례와 실패사례에 대한 정성적인 분석을 진행했는데, 성공한 케이스에서는 보상곡선이 완만하게 우상향하는 경향을 보인 반면 실패사례에서는 평평한 개형을 보였다고 함.

그리고 WEB-SHEPHERD가 이상한 행동을 한 케이스를 정리했는데, 필요한 행동임에도 당장 도움이 되는것같지 않으면 점수를 짜게 주는 근시안적인 모습도 보였고, 전체적인 맥락을 놓쳐서 의미없는 루프에 빠지는 경우도 있었고, 체크리스트를 만들때 할루시네이션이 생겨서 없는 작업을 하라고 시킨다던지 했다고 함.

---

## 8. Conclusion
