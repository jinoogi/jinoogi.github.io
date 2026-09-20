---
title: Tree search agent 리뷰
date: 2026-09-20 00:49:00 +0900
categories: [AI Paper Reviews, Agents]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Tree search for language model agents**<br>
Date: 2024.7.1<br>
Venue: TMLR<br>
Notable author: -<br>
Comprehension:  2.9단계

</div>
</div>

## 0. Abstract

![타임스텝마다 후보 A~E 중 가치가 높은 가지만 골라 확장해 나가는 트리 탐색(beam search) 예시 그림](/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig1.png)

이 연구는 web agent에서 test-time scaling을 적용한 연구임.
근데 단어를 생성하는 일반적인 언어모델링에서 상황이 다른게, 거기선 상태전이확률이 필요가 없어서 그냥 LLM이 트리를 스스로 뻗으면서 탐색할 수 있었다고 한다면 web agent에서는 웹의 상태전이확률을 모르기때문에 실제 웹에서 실행을 하는방식으로 탐색한다고 함.
그렇게 test-time scaling을 적용했더니 WebArena라는 도전적인 환경에서 상당한 성능향상이 있었음.

---

## 1. Introduction

WebArena같은 실전적인 문제에서 기존의 LLM 기반 agent들은 인간이 80~90%의 성공률을 보이는데 반해 프론티어 agent들이 20%에 머무르는등 죽을 쑤고 있었다고 함.
저자들은 웹 환경이 복잡한데 반해 기존 agent들이 test time에 탐색을 전혀 하지 않는다는점을 지적함.
모델 기반 가치함수를 사용해서, 이 web navigation task에서 효과적으로 탐색을 수행하는 방법을 제안함.

---

## 2. Background

### 2.1 Realistic simulated web environments

크게 3가지로 기존의 벤치마크들을 구분함.
시뮬레이션 없이 HTML로 정적으로 평가하는 Mind2Web이나 VisualWebBench.
시뮬레이터를 통해 동적으로 평가하는 MiniWoB, WebShop, WebLINX, MMInA, **OSWorld**, **WorkArena**
진짜 현실과 동일한 시뮬레이터를 쓰는 WebArena, VisualWebArena 등…

<figure style="width:40%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig2.png" alt="논문 Table 1: (Visual)WebArena 환경에서 가능한 action 목록 (click, hover, type, press, new_tab, goto, scroll, stop 등)" style="width:100%;">
</figure>

자기들은 (Visual)WebArena가 가장 현실적이므로 이 벤치마크를 사용한다고 함.

### 2.2 Language-guided autonomous agents

web navigation 분야는 LLM이 나오기 전에는 장난감환경에서 RL이나 모방학습으로 주로 학습하는경우가 많았는데 일반화도 처참하고 성능도 구렸다고 함.
그러다가 23년쯤 GPT-3같은 LLM이 나오면서 LLM을 써봤더니 프롬프팅이나 간단한 fine-tuning만으로도 상당히 잘한다는걸 발견함.
그러면서 LLM에 피드백이나 외부지식들을 사용하는 등 점점 LLM방법론들도 고도화됐고, LLM을 이미지도 사용하는 멀티모달로 확장하게 되었다는 흐름 정리.

### 2.3 Search and planning

BFS,DFS,A*부터 MCTS까지 다양한 탐색알고리즘을 언급하는데, 자기들은 복잡하고 현실적인 실제 웹사이트 환경에서 탐색을 수행한다는 이야기.

---

## 3. Method

### 3.1 Agent backbone

자기들이 제안하는 방법은 프롬프팅기반 agent든 fine-tuning기반 agent든 어떤 backbone을 쓰든간에 사용 가능한 방법론이라 아무거나 써도 된다고함.

### 3.2 Value function

<div style="display:flex; gap:12px; align-items:center;">
  <figure style="width:66%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig3.png" alt="논문 Figure 11: value function에 쓰인 system message와 프롬프트 전문" style="width:100%;">
    <figcaption style="text-align:center; font-size:0.85em; color:gray;">
      Value model input
    </figcaption>
  </figure>
  <div style="width:32%; display:flex; flex-direction:column; gap:12px;">
    <figure style="width:100%; margin:0;">
      <img src="/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig4.png" alt="논문 Figure 7: SoM 에이전트 정책 모델의 system prompt 전문" style="width:100%;">
      <figcaption style="text-align:center; font-size:0.85em; color:gray;">
        Policy model system prompt
      </figcaption>
    </figure>
    <figure style="width:100%; margin:0;">
      <img src="/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig5.png" alt="논문 Figure 8: SoM 에이전트 정책 모델의 few-shot 예시와 프롬프트" style="width:100%;">
      <figcaption style="text-align:center; font-size:0.85em; color:gray;">
        Policy model few-shot
      </figcaption>
    </figure>
  </div>
</div>

가치함수는 LLM을 통해서 구현했는데, $$v_t=f_v(I,\{o_1,...,o_t\})\in[0,1]$$ 이렇게 지금관측뿐만 아니라 과거관측까지 넣어줌.
근데 저거 구라임. 이 장에서 너무 대충설명해서 부록과 4장의 내용까지 보면, 사실 저것뿐만아니라 행동들도 같이 넣어주고, 점수도 연속적으로 출력되는게 아니라 $$\{0,0.5,1\}$$ 이렇게 discrete한 값을 사용함.
실패일때는 0점, 맞는 trajectory로 가고있을때는 0.5점, 성공했을때는 1점 이렇게
근데 우선순위큐를 사용하는데 저렇게 작게 discretize하면 서열정리에 장애가 생기는거 아닌가? 했음.
그래서 한번만 가치를 평가하는게 아니라 20번 평가해서 평균을 내는 self-consistency 방법을 사용함.
이렇게 하면 coarse했던 가치점수가 fine해지면서 그 우려가 줄어듦.

정책모델은 입력으로 시스템프롬프트랑 few-shot들 넣어주고, 상태와 직전 행동을 넣어주는것같음.

### 3.3 Search algorithm

![논문 Figure 1: 제안한 탐색 알고리즘 - 탐색 없는 GPT-4o 에이전트의 실패와, 가치함수 점수와 backtracking으로 성공하는 GPT-4o 에이전트 + Search 비교](/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig6.png)

탐색알고리즘은 best-first 알고리즘인데, 한마디로 말하면 우선순위큐에 관측들의 가치를 넣어놓고 높은애부터 가보는데, 과거로 돌아갈수 있는 기능도 있는 알고리즘임.

![논문 Algorithm 1: step t에서의 탐색 알고리즘 의사코드 (우선순위 큐 기반 best-first search)](/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig7.png)

근데 이상하게 $$s_p \rightarrow a_p^i \rightarrow s_p^i$$ 이렇게 미래 상태를 $$s_{p+1}$$이 아니라 그냥 $$s_p^i$$ 로 표시하고, 그걸로 바로 가치함수를 계산하는게 아니라 걍 상태를 업데이트한다고 함.
근데 상태가 진짜 상태가 아니라 행동의 시퀀스를 말하는거임. 표현이 모순같고 개떡같은데 $$a_0,a_1,...,a_p^i$$ 이렇게 행동을 추가하는게 상태를 업데이트하는게 된다고 함.
다시 봐도 정말 표현이 개떡같은데 $$s_p^i$$는 진짜 상태가 아님.
저건 그냥 행동들의 시퀀스 $$a_0,a_1,...,a_p^i$$이고, 웹 브라우저에서 실행해서 진짜 상태가 되는건 line8에서임…
웹에서 뒤로가기가 안먹히는경우가 많아서 만약 진짜정석대로 line23에서 웹브라우저에서 찐으로 실행을 해버렸다가 뒤로가기가 이상하게 작동하면 골치아프다고 함.
그리고 진짜 상태를 저장하는건 용량이 너무 크고 어차피 환경이 결정론적이니까 행동시퀀스만 갖고있어도 똑같이 재현된다는 장점도 있다고 하는듯.
어쨌든 그래서 가치함수 계산을 정석대로 못하기때문에 우선순위큐에 넣을때 자기 가치함수가 아니라 부모 가치함수대로 넣어지고, 실제 알고리즘이랑 다른 이상한 알고리즘이 되버리는듯.

---

## 4. Experiments

### 4.1 Implementation details

탐색의 하이퍼파라미터부터 보면, 최대행동의 깊이 $$d=5$$, 실행해보는 행동의 개수 $$b=5$$ , 전체 노드개수(실제로 웹 실행하는거) $$c=20$$으로 설정함.
$$d=5$$라는 말은 최대 행동의 깊이가 5스텝이라는말인데, 보통 hard난이도는 10번 이상의 행동을 요구하므로 이렇게 되면 long-horizon task를 해결못함.

행동을 생성할때는 $$\text{top-p}=0.95$$를 사용했는데, 이건 토큰 디코딩할때 이야기라 $$b=5$$랑 모순되는게 아님!
$$b=5$$도 행동을 딱 5개만 생성하는게 아니고 20개를 샘플링한다음에 거기서 빈도순으로 5개를 필터링하는 로직.

```
click [id=5] 8표, 
click [id=71] 3표, 
go_back 2표, 
tab_close 1표, 
click [id=11] 1표
scroll [up] 1표
...
```

가령 샘플링결과가 이런식이면, 상위 5개의 action만 쓰도록 필터링하는거임.

### 4.2 Results

![논문 Table 2: VisualWebArena와 WebArena에서 baseline과 탐색 적용 모델의 성공률 및 상대 변화](/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig10.png)

보면 확실히 best-first로 test-time scaling을 했을때 성능이 유의미하게 뛰는걸 알 수 있음.
한 30%정도가 뛴다고 보면 맞을것같고, Llama-3 같은경우는 멀티모달모델이 아니기때문에 VWA에서는 이미지를 caption으로 변환했다고 함.

---

## 5. Analysis

### 5.1 Ablations

**Search budget**

![논문 Figure 2(search budget에 따른 성공률)와 Table 3(탐색 깊이 d와 branching factor b에 따른 성공률)](/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig11.png)

탐색 하이퍼파라미터 $$b,d,c$$을 바꿔보면서 스케일링했을때 얼마나 효과적인지 실험해봄.
결과는 위와같이 모든 파라미터가 다 스케일링했을때 성능을 올린다는것을 확인함.

**Varying the value function**

<figure style="width:63%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig12.png" alt="논문 Table 4: value function 종류에 따른 GPT-4o 에이전트의 성공률" style="width:100%;">
</figure>

value function에 이런저런 장난을 치면서 바꿔봄.
LLaVA라는 오픈소스모델을 value model로 사용해봤는데 이건 이미지가 하나밖에 안들어가는 애라서 현재상태밖에 못주고, GPT-4o를 value model로 썼을때보다 안좋았음.

GPT-4o 같은 신경망이 아니라 그냥 규칙기반으로 실제 정답인지 여부를 value funtion으로도 써봤는데, 그렇게 하면 맞는 trajectory일때도 0.5점이 아니라 0점임.
그냥 딱 정답스텝만 1이고 나머지는 0인 coarse한 애가 되는데다가 불확실성이 존재하지 않아서 self-consistency가 아무 의미가 없고 따라서 점수도 fine해지지가 않음.
그래서 과정을 전혀 가이드 못해주는데도, 오히려 점수가 크게 오름…
value function에 개선할 여지가 많이 남아있다는걸 알 수 있음.

마지막으로 self-consistency를 제거한버전도 써봤는데, 성능이 크게 떨어졌음.
value function이 coarse하고 불안정한걸 self-consistency라는 몬테카를로 추정으로 커버하고있었으니 어찌보면 당연한 결과인듯.

**Comparison to trajectory level reranking**

<figure style="width:63%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig13.png" alt="논문 Figure 3: trajectory 수에 따른 trajectory re-ranking 방식의 성공률과 tree search 비교" style="width:100%;">
</figure>

여기서는 test-time scaling 쓰는게 좋은건 알겠는데, best-first말고 그냥 일반적인 scaling 방법 쓰면 안되는지 테스트해봄.
best-of-N이랑 비교해봤는데, 솔직히 저자들 주장대로 성능이 크게 차이가 나는건 아닌것같지만 백트래킹 없이 끝까지 다 rollout해야되기 때문에 환불안되는 상품을 구매한다던지 그런 파괴적이고 잘못된 행동을 했을때 되돌릴수가 없다는 단점이 존재함.

### 5.2 Success rate breakdown

<figure style="width:72%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Tree-search-agent/tree-search-agent-fig14.png" alt="논문 Table 5: 난이도(easy, medium, hard)별 GPT-4o 에이전트의 탐색 유무에 따른 성공률" style="width:100%;">
</figure>

성능향상을 좀더 granullar하게 점수대별로 보는데, 쉬운과제는 정답 traj가 3스텝 이하, 중간과제는 4~9스텝, 어려운과제는 10스텝 이상으로 분류함.
그랬더니 중간난이도정도의 과제에서 가장 높은 성능향상이 있었음.

### 5.3 Qualitative results

tree search를 사용했을때 그냥 직선으로 행동하던 기존 agent들보다 훨씬 강건했다고 함.
원래 기존 agent들도 실패했을때 뭐라고 해보려고 발버둥치는 경우들이 많은데, 무한루프에 빠지거나 어거지로 끝까지 이상한곳으로 빠져버리는식의 실패가 흔했다고 함.
근데 이 best-first방식의 search를 하면 우선순위큐에서 pop을 해버리니까 똑같은 action sequence를 반복할수가 없고, 구린것같으면 백트래킹으로 돌아갈 수 있어서 훨씬 강건함.
아니 그럼 얘는 action sequence가 각자 다 unique하니까 이론상 절대 무한루프 안빠지는거 아닌가? 했는데, action sequence가 각자 다 unique해도 action의 기능이 사실상 겹치는게 있을 수 있어서 같은 상태로 빠질수도 있기때문에 무한루프로부터 완전 해방은 아니라고 함.

### 5.4 Limitations

논문의 한계로 계산비용이 상당히 높고, 비가역적인 파괴적 행동을 막는 특별한 로직이 없다는점, 그리고 가치함수가 task-specific하게 설계되었다는점을 인정함.

---

## 6. Conclusion

best-first 탐색을 이용해 현실적인 웹 환경에서 작동하는 agent 성능을 유의미하게 향상시킨 test-time scaling 방법이라고 기여점 밝히고 마무리

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>🦅</div>
<div markdown="1" style="flex:1; min-width:0;">

**전체적인 방법론**<br>
어떤 상태에서 정책모델을 이용해 20개의 action들을 샘플링하고 voting으로 상위 5개의 action만 필터링.<br>
5개의 action들을 실행해서 다음 상태로 만들고, 가치함수모델로 평가.<br>
이때 가치함수모델은 coarse한 점수를 주지만 20번 self-consistency를 통해 fine하고 실제 가치에 가까운 점수로 만듦.<br>
우선순위큐에 push하는데 과거로 돌아가는 backtracking도 사용 가능해서 웹이라는 환경에 제약받지않고 우선순위큐의 특성 그대로 살릴 수 있고, 가치가 높은 상태들을 효과적으로 탐색할 수 있음

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>😲</div>
<div markdown="1" style="flex:1; min-width:0;">

**느낀점**<br>
와… 근데 너무 비효율적인것같음<br>
무슨 정책모델로 action 샘플링할때도 Instruction이랑 action space랑 few-shot이랑 현재관측이랑 과거 행동내역 넣고, 가치를 평가할때도 마찬가지로 과거 행동이랑 과거 관측들이랑 Instruction이랑 꾸역꾸역 넣은걸 또 Self-consistency 때문에 모델을 20번씩 돌리고…<br>
컨텍스트가 남아날지 모르겠음… 돈도 대체 얼마나 깨질지 무섭고<br>
거기가 가치함수 성능도 처참해서, 나름 dense한 모델임에도 불구하고 sparse한걸 썼을때보다 성능이 한참 모자람…<br>
그리고 무엇보다도 예상이 아니라 실제 실행을 하면서 탐색을 하기때문에 너무 비싸고 비효율적임.<br>
그냥 GPT에서 언어모델링할때의 탐색은 장점이 뚜렷했는데, 이런식으로 사실상 현실에서 탐색하는 방법은 솔직히 뭔가 좀…

</div>
</div>
