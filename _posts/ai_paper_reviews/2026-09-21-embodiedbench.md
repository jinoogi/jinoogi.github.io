---
title: EmbodiedBench 리뷰
date: 2026-09-21 01:07:00 +0900
categories: [AI Paper Reviews, Embodied AI]
math: true
---

<div style="display:flex; gap:12px; background:rgba(135,131,120,0.15); padding:16px 20px; border-radius:8px; margin:16px 0;">
<div>💡</div>
<div markdown="1" style="flex:1; min-width:0;">

**EMBODIEDBENCH: Comprehensive Benchmarking Multi-modal Large<br>
Language Models for Vision-Driven Embodied Agents**<br>
Date: 2025.6.5<br>
Venue: ICML2025 oral<br>
Author: Rui Yang et al (UIUC)

</div>
</div>

## EmbodiedBench 오버뷰

![논문 Figure 1: EmbodiedBench 개요 - 고수준(EB-ALFRED, EB-Habitat)과 저수준(EB-Navigation, EB-Manipulation) 행동 환경, 그리고 Base Capability, Common Sense, Complex Instruction, Spatial Awareness, Visual Appearance, Long Horizon 6가지 역량별 평가](/assets/img/ai_paper_reviews/EmbodiedBench/embodiedbench-fig1.png)

High level: EB-ALFRED, EB-Habitat
Low level: EB-Navigation, EB-Manipulation

환경을 4가지로 분류하고 그 안에서 다시 필요역량 6가지로 task를 분류함.

|  | Base Capability | Common Sense | Complex Instruction | Spatial Awareness | Visual Appearance | Long Horizon |
| --- | --- | --- | --- | --- | --- | --- |
| ALFRED | 50 | 50 | 50 | 50 | 50 | 50 |
| Habitat | 50 | 50 | 50 | 50 | 50 | 50 |
| Navigation | 60 | 60 | 60 | - | 60 | 60 |
| Manipulation | 48 | 48 | 48 | 48 | 36 | - |

#### EB-ALFRED

`"slice a tomato, heat it up in the microwave, and place it in the sink”`
AI2-THOR 시뮬레이터를 기반으로 만들어진 Lota-Bench를 수정해서 만듦.
("pick up", "open", "close", "turn on", "turn off", "slice", "put down", "find") 같은 고수준 행동에 대상물체를 붙여서 “pick up apple” 이렇게 작동하는 방식인데, 잡다한 버그를 수정하고 동일한 물체가 있어도 사용할수 있도록 cabine1, cabinet2처럼 인덱스를 붙여줌.
행동결과와 원인까지 알려주는 풍부한 피드백 존재

#### EB-Habitat

`"Move the spoon to the brown table, the sponge to the brown table, and the cleanser to the black table”`
이건 Habitat2라는 시뮬레이터를 기반으로 함.
action은 ALFRED처럼 조합하는 형식이 아니라 대상까지 다 고정되어있는 70개의 aciton중에서 고르는 방식.
(navigation, pick, place, open, close)의 범주로 분류되는데, “find apple”로 어디로든 다 찾아갈수 있는 ALFRED와 달리 habitat는 가구나 장소로만 찾아갈수 있음.
마찬가지로 행동결과와 원인까지 알려주는 풍부한 피드백 존재

#### EB-Navigation

`"navigate to the Pot in the room and be as close as possible to it”`
찾아가는 네비게이션 작업만 보는 환경.
ALFRED처럼 AI2-THOR 시뮬레이터기반으로 만들었는데, 대신 저수준행동버전임.
전후좌우 움직임이랑 상하좌우 회전 이렇게 8가지 행동이 가능.
피드백은 딱 행동결과만 짧게 알려줌.

#### EB-Manipulation

`"Stack the front star on top of the right cylinder”` 
얘는 나머지 환경과 달리 집이 아니라 CoppeliaSIm 시뮬레이터에서 로봇팔을 제어하는 환경임.
근데 MLLM이 이미지를 보고 직접 좌표를 추정하는걸 너무 못해서, 실수좌표가 아니라 이산적인 정수좌표만 출력하면 자세한 조작은 시뮬레이터가 하게 바꾸고, YOLO로 바운딩박스를 쳐서 자세한 좌표까지 알려준다고 함.
