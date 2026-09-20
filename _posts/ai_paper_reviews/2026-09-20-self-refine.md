---
title: SELF-REFINE 리뷰
date: 2026-09-20 00:51:00 +0900
categories: [AI Paper Reviews, Agents]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**SELF-REFINE: Iterative Refinement with Self-Feedback**<br>
Date: 2023.3.30<br>
Venue: NeurIPS 2023<br>
Notable author: -<br>
Comprehension: 3단계

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>😲</div>
<div markdown="1" style="flex:1; min-width:0;">

**느낀점**<br>
분명 참신한방법이긴 한데, task별로 편차가 엄청나게 크다는점이 신경쓰임.<br>
특히 7가지 벤치마크중에 GSM-8k말고는 다 자기들이 창작하다시피 한 권위없는 메트릭인데, GSM-8k에서는 성능향상이 거의 없다시피한점이 아쉬움.

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>🦅</div>
<div markdown="1" style="flex:1; min-width:0;">

**전체적인 view**<br>
사람이 글쓰듯이 LLM의 생성을 바로 쓰는게 아니라 feedback하고 refine하는걸 반복해서 더 좋게 만드는데, feedback과 refine도 프롬프팅을 통해 동일한 LLM으로 만들게 함.

</div>
</div>

## 0. Abstract

인간이 반복적으로 글을 다듬으며 발전시키는것을 LLM에 그대로 적용한 연구.
하나의 LLM을 generator, refiner, feedback provider로 사용하기때문에 별다른 학습이 필요없는 test-time scaling 방법이며, 성능도 좋았다고 함.

---

## 1. Introduction

![논문 Figure 1: SELF-REFINE 개요 - 같은 모델 M이 자기 출력에 feedback을 주고, 그 feedback으로 이전 출력을 refine하는 반복 루프](/assets/img/ai_paper_reviews/SELF-REFINE/self-refine-fig1.png)

이때는 프론티어 LLM인 GPT-3.5, 4 도 원큐에 복잡한 요구사항을 만족하는 출력을 잘 만들어내지 못했던것같음.
그래서 이 생성품질을 향상시키기 위한 일환으로 보통은 보상모델을 이용하거나 했는데, 자기들은 인간에서 모티베이션을 얻어 요렇게 단순하고 복잡하지도 않은 방법론을 만들어냄.

그렇게 했더니 텍스트생성에서는 5~40%p, 코드생성에서는 10%p라는 엄청난 성능향상이 있었다고 함.

---

## 2. Iterative refinement with self-refine

![논문 Algorithm 1: SELF-REFINE 알고리즘 의사코드 (초기 생성, feedback, 정지 조건, refine)](/assets/img/ai_paper_reviews/SELF-REFINE/self-refine-fig2.png)

feedback과 refine은 프롬프팅을 통해 유도함.

여기서 $$\vert\vert$$ 는 조건부확률이나 KL 다이버전스같은게 아니라 문자열 이어붙인다는 뜻.
그리고 특이하게 refine은 $$\mathcal{M}(p_{\text{refine}}\vert\vert x\vert\vert y_t\vert\vert fb_t)$$ 이런식으로 해당 스텝의 정보만 사용하는게 아니라 전체 trajectory를 다 줘서 $$\mathcal{M}(p_{\text{refine}}\vert\vert x\vert\vert y_0\vert\vert fb_0\vert\vert ...\vert\vert y_t\vert\vert fb_t)$$ 이런식으로 생성하게 함.

---

## 3. Evaluation

<div style="display:flex; gap:12px; align-items:center;">
  <figure style="width:37%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/SELF-REFINE/self-refine-fig3.png" alt="논문 Table 4: 평가에 쓴 7개 task의 설명, 데이터셋, FEEDBACK-REFINE 한 번의 예시" style="width:100%;">
  </figure>
  <figure style="width:61%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/SELF-REFINE/self-refine-fig4.png" alt="논문 Table 1: GPT-3.5, ChatGPT, GPT-4를 base로 한 여러 task에서의 SELF-REFINE 결과" style="width:100%;">
  </figure>
</div>

이런 벤치마크에서 성능을 측정한다고 하는데, GSM-8k말고는 정식 벤치마크가 아니라 자기들이 만들어낸거임.

Math reasoning, Code optimization, Constraint generation에서는 Task별로 정의된 metric으로, 
Dialogue response, Code readability, Sentiment reversal, Acronym generation은 사람/GPT의 선호도로 채점했다고 함.

그리고 평가 결과 모든 테스트 메트릭에서 성능이 향상됨을 관측했는데, GSM-8k에서는 성능향상이 미미했음.

---

## 4. Analysis

**feedback 품질의 영향:**

![논문 Table 2: SELF-REFINE feedback, generic feedback, feedback 없음의 성능 비교](/assets/img/ai_paper_reviews/SELF-REFINE/self-refine-fig5.png)

feedback의 중요성을 확인하기 위해 구체성 없이 그냥 잘하라는 느낌의 generic feedback으로 갈아끼웠을때와 아예 feedback없이 루프를 돌리는 ablation을 해봤음.
그 결과, 저런식으로 성능이 점점 떨어졌고,  feedback의 품질이 유의미하게 영향을 미친다는거 확인.

**feedback-refine 반복횟수의 영향:**

![논문 Figure 4: iteration별 점수 향상(왼쪽 표)과 반복에 따른 향상폭 감소(오른쪽 막대그래프)](/assets/img/ai_paper_reviews/SELF-REFINE/self-refine-fig6.png)

요런식으로 반복할수록 성능이 향상되긴 했는데, 수익체감법칙이 있어서 점점 상승폭이 둔화된다고 함.

**다른 test-time scaling과의 비교:**

![논문 Figure 6: SELF-REFINE 출력과 다중 샘플 baseline(MULTI) 출력에 대한 선호도 비율 (Sentiment Reversal, Acronym Generation)](/assets/img/ai_paper_reviews/SELF-REFINE/self-refine-fig7.png)

그냥 SELF-REFINE 방법론이 뛰어난게 아니라 test-time scaling 이 돼서 성능이 올라간거 아냐? 라는 의문에 답하기위해 1 vs k라는 강화된 best-of-N이랑 비교함.
보상모델이 찍어준 최강자랑 붙는게 아니라 k개랑 전부 다 붙어야하는 더 어려운 조건이었는데도 SELF-REFINE이 선호도가 훨씬 높았음. 
그래서 피드백에 기반한 반복자체가 핵심이라는거 입증

**모델이 안좋아도 SELF-REFINE이 잘 작동할까?:**
GPT같은 똑똑한애들말고 Vicuna-13B라는 애로 실험해봤는데 망했음.
SELF-REFINE도 결국 자기성찰이랑 지시따르기 능력이 받쳐줘야 가능한 테크닉이라는점 확인

**정성분석:**
SELF-REFINE의 실패지점을 분석해보니 대부분 refine이 아니라 feedback이 잘못생성되는것이 병목으로 작용했다는 분석.

---

## 5. Related work

기존 feedback 연구들 언급하면서 다른애들은 스칼라 보상함수를 쓰거나 별도로 훈련을 하거나 하는 특정 task 특화 방식이었는데 자기들은 자연어 피드백을 제공하면서도 별도 훈련이 필요없는 범용 feedback 모델이라는 점.

---

## 6. Limitation and discussion & 7. Conclusion

SELF-REFLECTION의 한계로는 모델이 어느정도 똑똑해야 먹히는 방법이라는점이라는거임.
다만 하나의 LLM만으로도 간단히 구현할수 있는 효과적인 방법론이라고 기여를 밝히며 마무리
