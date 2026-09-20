---
title: Batchnorm & Layernorm 리뷰
date: 2026-09-20 00:03:00 +0900
categories: [AI Paper Reviews, CV & Multimodal]
math: true
---

# Batch Norm

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift**<br>
Date: 2015.2.11<br>
Venue: ICML 2015<br>
Notable author: 작성자 전원<br>
Comprehension: 2단계

</div>
</div>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

**느낀점**<br>
경고: 특이하게도 이 논문은 일반적인 노테이션과 반대로 윗첨자를 특징의 노드번호, 아랫첨자를 데이터의 인덱스로 사용함. 근데 나는 원래대로 정상적인 표기법으로 적을거임.<br>
저자들이 주장한 batch normalization의 효과가 몇가지 있는데, 일부는 사실이고 일부는 사실이 아니라고 밝혀졌다고 함.

- BN은 내부 공변량 이동을 잡아준다! ❌ : 후속연구에서 BN이 공변량이동을 거의 못잡아줬다고 함<br>
  whitening도 아니고 그냥 배치단위의 평균과 분산만 맞추는정도는 고차원분포의 분포를 제대로 안정화시킬수 없었다고 함.
- BN쓰면 드롭아웃 안써도 되고, 학습률 높여도 안터진다! ✅
- BN쓰면 초기화에 별로 신경 안써도 된다! ✅
- BN은 활성함수 이전에 넣어야한다! ❌: 뒤에넣었을때 성능이 오르는경우도 있다고 함.

</div>
</div>

## 0. Abstract & 1. Introduction

<figure style="width:46%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Batchnorm-Layernorm/batchnorm-layernorm-fig1.png" alt="은닉층 3개짜리 MLP 구조" style="width:100%;">
</figure>

아래층에서 조금만 파라미터를 수정해도 변화가 누적되어서 위의층 입력은 분포가 요동침.
가령, 이전 배치에는 5층에서 [1.2, -0.2 , 3] 이런식의 데이터가 들어왔는데, 이번 배치에는 갑자기 [21.2, 2.9 , -9] 이런 입력이 들어오는거임.

가령 $$\ell=F_2(F_1(\mathbf{u}_0,\Theta_1),\Theta_2)$$ 이렇게 2개 레이어층의 신경망을 고려할때, $$\mathbf{u}_1=F_1(\mathbf{u},\Theta_1)$$ 로 보면 $$F_2$$입장에서는 그냥 입력이 $$\mathbf{u}_1$$으로 들어오는 신경망 훈련임.
근데 $$u_1$$은 시간에 따라 분포가 변하므로, 학습에 애로사항이 생김.
이렇게 시간에 따라 입력의 분포가 변하는문제를 공변량 이동이라고 부름.

![시그모이드 도함수 그래프: 0에서 멀어지면 기울기가 소실됨](/assets/img/ai_paper_reviews/Batchnorm-Layernorm/batchnorm-layernorm-fig2.png)

거기다가, 시그모이드같은 활성함수는 0 부근에서 벗어나면 그라디언트값이 소실되는 문제도 있음.

## 2. Towards reducing internal covariate shift

그래서 저 공변량 이동을 막기위해 매 레이어마다 입력을 whitening하는 방법을 생각해봤음.
그렇게 하면 데이터의 다변량통계가 완전히 구형인 데이터로 되므로, 공변량 이동 문제도 해결되고 아주 이상적으로 분포가 고정됨.

<div style="display:flex; gap:16px; align-items:center;">
  <figure style="width:34%; margin:0;">
    <img src="/assets/img/ai_paper_reviews/Batchnorm-Layernorm/batchnorm-layernorm-fig3.png" alt="가중합과 활성화 사이에 BN이 들어간 신경망 손그림" style="width:100%;">
  </figure>
<div markdown="1" style="width:64%;">

$$
X =\begin{bmatrix}x_1^{(1)} & x_2^{(1)} & \cdots & x_d^{(1)} \\x_1^{(2)} & x_2^{(2)} & \cdots & x_d^{(2)} \\\vdots    & \vdots    & \ddots & \vdots \\x_1^{(m)} & x_2^{(m)} & \cdots & x_d^{(m)}\end{bmatrix}\in \mathbb{R}^{m \times d}
$$

</div>
</div>

whitening은 $$\hat{\mathbf{x}}=Cov[\mathbf{x}]^{-1/2}(\mathbf{x}-E[\mathbf{x}])$$ 이렇게 정의되는데, 계산그래프에 이 정규화과정을 정석적으로 넣으면 역전파할때 이걸 미분해야하는데 연산량이 엄청나서 쓸수가 없다고 함.
그래서 계산그래프상에서 정석적으로 넣는게 아니라 그냥 외부에서 공분산행렬이랑 평균벡터를 계산해서 넣어주는방법을 써봤는데, 그렇게하면 정규화(whitening)과정의 계산그래프가 끊기는바람에 최적화알고리즘이 정규화를 인지하지못하고 계속 파라미터를 업데이트하는 기울기 폭발 문제가 생겼다고 함.

<details markdown="1">
<summary>예전설명</summary>

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>📋</div>
<div markdown="1" style="flex:1; min-width:0;">

잘못된 설명이 있지만 그래도 직관적이라 이해를 도와줌

</div>
</div>

정규화도 최적화파라미터로 관리하는 대상으로 설정해야함.<br>
왜냐면 정규화와 최적화가 따로 논다면, 파라미터를 수정해도 손실을 줄이려고 해도 정규화가 그 노력을 상쇄시켜버리므로 손실이 줄어들지도 않는데 기를쓰고 손실을 줄이려고 계속 파라미터가 무한히 업데이트됨.

$$x=u+b$$ 에서 손실을 줄이려고 편향 $$b$$ 를 $$b+\Delta b$$로 업데이트해봤자 $$E[x]$$도 $$\Delta b$$ 만큼 커지므로 업데이트의 효과가 상쇄되어버리는 예시를 생각하면 직관적임.

근데 만약 최적화가 정규화를 인식하고 있다면, 위의 예시에서 자기가 $$\Delta b$$만큼 업데이트해도 상쇄돼서 손실함수에 영향을 못주는걸 알게돼서 업데이트도 안하고, 기울기폭발문제도 방지됨.

<figure style="width:82%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Batchnorm-Layernorm/batchnorm-layernorm-fig4.png" alt="정규화가 포함된 계산그래프와 입력별 정규화 손그림" style="width:100%;">
</figure>

“정규화를 모델 내부에서 수행하는데 당연히 인식하지 왜 못함?” 싶었는데, 연구자들도 바보가 아니라서 당연히 알고 있었지만 정규화 부분을 체인룰로 미분하려면 계산그래프가 저렇게 다 연결되어있어서 미분할때 저렇게 야랄맞은 $$\hat{x}$$ 식을 미분해줘야했다고 함.<br>
근데 이게 너무 연산비용이 엄청나서, $$\mu, \sigma$$를 정석적으로 파라미터로 나타내는게 아니라 울며겨자먹기로 계산을 끝낸 상수값을 썼다고 함.<br>
그러니까 이제 계산그래프가 끊겨서 최적화가 정규화과정을 전혀 인식하지 못하고 파라미터 폭발이 일어나고 그랬던거임.

$$
\hat{x}_i = \frac{x_i - \mu}{\sigma}\
=\frac{x_i - \frac{1}{d} \sum_{j=1}^{d} x_j}{\sqrt{\frac{1}{d} \sum_{j=1}^{d}\left(x_j - \frac{1}{d} \sum_{k=1}^{d} x_k\right)^2}} \\
\text{where} \quad \mu= \frac{1}{d} \sum_{j=1}^{d} x_j, \;
\sigma^2 = \frac{1}{d} \sum_{j=1}^{d} (x_j - \mu)^2
\hat{x}_i
$$

</details>

## 3. Normalization via mini-batch statistics

그래서 이상적인 다변량정규화인 whitening은 포기하고, 배치끼리만 정규화를 수행하는 batch normalization으로 방향을 전환함.

물론 whitening에 비하면 불완전하고 공분산 텀이 살아있지만, 그것만으로도 수렴속도가 올라간다는것이 입증되어있다고 함.

입력 $$\mathbf{x}=\{x_1,x_2,...,x_k\}$$가 있을때 $$\hat{x}_k=\frac{x_k-E[x_k]}{\sqrt{Var[x_k]}}$$ 으로 정규화.
처음엔 입력의 특성끼리 정규화한다는줄 알고 헷갈렸는데, 그게아니라 $$k$$번째 특성 $$x_{k}$$을 잡고 $$\{x_k^1,x_k^2,...,x_k^m\}$$이렇게 배치끼리 정규화하는거라고 함.

그리고 Batch Normalization layer에서는 먼저 배치단위 정규화를 하고, $$y_k=\gamma \hat{x}_k+\beta$$ 를 해주는 연산이 포함되어있다고 함.

![BN 레이어 내부: batch normalize 후 scale and shift를 거쳐 활성화로 가는 구조 손그림](/assets/img/ai_paper_reviews/Batchnorm-Layernorm/batchnorm-layernorm-fig5.png)

“아니 왜 힘들게 정규화해놓고 다시 도루묵시키는거지? 공변량 이동이랑 그라디언트 소실이 문제라서 일부로 0 부근으로 정규화시켰잖아?” 싶었음.

비유적으로 보면 저 공변량이동과 그라디언트 소실은 ADHD같은거임.
통제할수 없이 특징값이 높았다낮았다 날뛰고 그라디언트가 활성화함수의 극단적인 부분에서 노는건 문제이지만, 어떨때는 그 극단적인 특징값이 필요할때도 있기때문에 저 문제 막겠다고 항상 0 부근에 가둬놓는건 안됨.
그래서 일단 디폴트로 약을 먹여서 시도때도없이 산만하던애를 먼저 진정시키되, 창의성이 필요한 작업에서는 ADHD를 켤 수 있게 스위치를 달아준거임.

이렇게 하면 지맘대로 ADHD가 도져서 아무것도 못하는 상황은 막되, ADHD의 힘을 쓰고싶을때는 사용할 수 있는 상황으로 만들어줄 수 있음.

그리고 $$\gamma, \beta$$는 학습가능한 파라미터라서, 역전파로 학습을 해줘야한다는 이야기.

추가로, $$\text{BN}(\mathbf{Wu}+\mathbf{b})$$ 이렇게하면 정규화때문에 bias의 영향은 사라지므로 bias를 제거해도 된다는 효과도 있다고 함.

### 3.1 Training and inference with batch-normalized networks

추론시에는 미니배치내의 다른 샘플들이 입력결과에 영향주면 안됨.
그래서  $$\hat{x}_k=\frac{x_k-E[x_k]}{\sqrt{Var[x_k]}}$$를 구할때 통계량을 미니배치 내의 샘플들로 구하는게 아니라 훈련때 봤던 데이터들로 전체 통계량을 구해놓은걸 사용함.

이렇게하면 추론때 배치에 샘플이 하나만 들어있는게 들어와도 분산을 못구해서 난리가 나지 않고 안정적으로 추론을 수행할 수 있다는 부가적인 효과도 있음.

### 3.2 Batch normalized convolutional networks

합성곱에서는 단순하게 생각해서 MLP에서처럼 픽셀별로 $$\hat{x}_k=\frac{x_k-E[x_k]}{\sqrt{Var[x_k]}}$$ 를 적용하면 합성곱의 형상이 깨져버린다고 함.
왜냐하면 픽셀별로 배치정규화를 진행하게되면, 픽셀별로 $$\gamma,\beta$$가 생기기때문에 이동불변성이 깨져버림.

그래서 평균과 분산같은 통계량을 구할때 샘플 수가 $$m$$개가 아니라 $$m'=m\times p \times q$$가 된다고 함.

### 3.3 Batch normalization enables higher learning rates

추가로, $$\text{BN}((\alpha\mathbf{W})\mathbf{u})=\text{BN}(\mathbf{Wu})$$ 이런 특징이 있는데, 이게 학습률설정을 잘못해서 파라미터 값이 엄청 올라가 폭발해버리는걸 막아준다고 함.

원래는 어떤 보폭으로 걸을지를 알아서 결정해준다는 뉘앙스인줄 알았는데, 그건 아니고 보폭(학습률)을 잘못설정해도 학습이 터지는걸 막아주는방식으로 도와준다고 함.

일단 기울기 폭발이 왜 일어나는지부터 보면

<figure style="width:85%; margin:0 auto;">
  <img src="/assets/img/ai_paper_reviews/Batchnorm-Layernorm/batchnorm-layernorm-fig6.png" alt="여러 층에 걸친 가중합과 활성화의 반복 구조 손그림" style="width:100%;">
</figure>

$$
\frac{\partial \mathcal{L}}{\partial \theta^{[l]}}=\frac{\partial \mathcal{L}}{\partial a^{[L]} } \cdot \underbrace{\frac{\partial a^{[L]}}{\partial z^{[L]}} \cdot\frac{\partial z^{[L]}}{\partial a^{[L-1]}}}_{\text{이부분 반복}} ... \frac{\partial a^{[l]}}{\partial z^{[l]}} \cdot \frac{\partial z^{[l]}}{\partial \theta^{[l]}}
$$

위의 식은 행렬이랑 실제 계산그래프 퍼지는거 무시하고 레이어별 연산을 보이기 위해 단순화 한 식인데, 활성화부분 $$\frac{\partial a^{[?]}}{\partial z^{[?]}}$$랑 가중합부분 $$\frac{\partial z^{[?]}}{\partial a^{[?-1]}}$$이 계속 반복적으로 곱해지는것을 알 수 있음.

근데 $$\frac{\partial z^{[?]}}{\partial a^{[?-1]}}$$ 이거 그냥 $$\theta^{[?-1]}$$ 이라서, 가중치가 계속 곱해지는거임.

그래서 기울기폭발의 매커니즘은, 가중치가 커지면서 1 이상인 값이 반복적으로 곱해지며 폭발하는 양상을 보였는데, 지금 batch normalization을 하면 

$$
\frac{\partial BN(\alpha \mathbf{Wu})}{\partial \mathbf{u}}= \frac{\partial BN(\mathbf{Wu})}{\partial \mathbf{u}}
$$

이렇게 가중치가 커져도 미분값이 가중치 스케일에 영향을 받지않게 됨.
위의 식으로 보면, $$\frac{\partial z^{[?]}}{\partial a^{[?-1]}}$$ 이 부분이 폭발하는 걱정에서 해방된거임.

두번째로 $$\frac{\partial z^{[l]}}{\partial \theta^{[l]}}$$ 이부분도 손봄.

가중치가 10배 커진 상태에서의 손실에 대한 그라디언트는 $$\frac{\partial L(10\mathbf{W})}{\partial (10\mathbf{W})}$$임.

근데 $$L(10\mathbf{W})=L(\mathbf{W})$$므로, 

$$
\frac{\partial L(10\mathbf{W})}{\partial (10\mathbf{W})}= \frac{\partial L(\mathbf{W})}{\partial (10\mathbf{W})}=\frac{\partial L(\mathbf{W})}{\partial (\mathbf{W})}\frac{\partial \mathbf{W}}{\partial (10\mathbf{W})}=\frac{1}{10} \frac{\partial L(\mathbf{W})}{\partial (\mathbf{W})}

$$

가 되어 오히려 미분값을 줄임.
”기울기폭발을 막았는데 굳이 왜 이런것까지 하는거지?” 했는데, 정규화가 도입된순간 가중치의 scale은 의미가 없고 학습은 가중치의 방향을 조정하는과정이라 가중치의 scale을 무력화하는 장치라고 함.

그래서 결론적으로는 기울기폭발에서 해방됨으로서 학습률을 높게 두는걸 두려워하지 않아도 되게 되었음.

### 3.4 Batch normalization regularizes the model

드롭아웃같은 효과도 존재함!
드롭아웃의 원리가 특정 노드에 과도하게 의존하지못하도록 노드를 없애버리는 강력한 노이즈를 부여하는건데, 배치 정규화를 사용하게되면 데이터가 결정론적으로 처리되는게 아니라 배치내의 다른 데이터들에 의해 확률론적인 노이즈가 생기게되면서 과적합이 해소됨.

---

# Layer norm

## 0. Abstract & 1. Introduction

batch norm은 효과적이지만 미니배치 크기에 의존하고, 특히 MLP 와 CNN 에는 어떻게 적용할지 연구되었지만 RNN에는 어떻게 해야하는지 모른다고 함.
그래서 샘플 하나의 통계량만 가지고 정규화를 수행하는 Layer norm 도입.

## 3. Layer normalization

![RNN을 시간축으로 펼친(unfold) 구조](/assets/img/ai_paper_reviews/Batchnorm-Layernorm/batchnorm-layernorm-fig7.png)

RNN에서 배치정규화가 왜 문제가 되냐면, RNN은 신경망 레이어 구조가 정해져있지 않고 입력에 따라 달라지는데, 그 입력도 정해져있지 않고 제각기 다르기때문임.

```
[나는, 고양이가, 좋다]
[딥러닝, 공부는, 정말, 재밌다]
[안녕]
```

가령 이런 배치가 있으면, t=1 에는 `[나는, 딥러닝, 안녕]` 이렇게 3개를 가지고 배치정규화가 되지만 t=2, t=3부터는 벌써 배치 크기가 2로 줄고, t=3에는 `[재밌다]` 밖에 없어짐…

심지어 추론때 `[이, 과정을, 직접, 따라가보니, 이해가, 잘, 되네요]` 같은게 들어오면, t=5,6 은 통계가 존재하지 않아서 작동자체가 안됨.

그럼 `<PAD>` 토큰을 써서 배치내의 모든 샘플길이를 맞추면 되는거 아닌가? 싶었는데, 그렇게되면 쓰레기정보가 차서 멀쩡했던 데이터가 정규화를 거치면 쓰레기가 되고 학습이 망함.

### 3.1 Layer normalized recurrent neural networks

RNN에서 입력(가중합)부분은 $$\mathbf{a}^t=\mathbf{W}_{hh}\mathbf{h}^{t-1}+\mathbf{W}_{xh}\mathbf{x}^t$$ 이렇게 되니까, 

$$
\mathbf{h}^t = f\Big[\frac{\mathbf{g}}{\sigma^t}\odot (\mathbf{a}^t-\mu^t)+\mathbf{b}\Big] \qquad \mu^t=\frac{1}{H}\sum_{i=1}^Ha_i^t \qquad \sigma^t=\sqrt{\frac{1}{H}\sum_{i=1}^H(a_i^t-\mu^t)^2}

$$

순서는 batch norm과 비슷하고, 대신 샘플 하나의 특성들로 통계량을 계산하므로 수식이 이렇게 바뀜.
layer norm도 마찬가지로 scale and shift를 수행하는데, $$\gamma,\beta$$ 대신 $$\mathbf{g},\mathbf{b}$$ 로 표현함.
