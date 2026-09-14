我会把 FitGround 彻底重写成一个**企业 AI 项目**，而不是“为了论文成立而设计的研究题”。

核心原则只有一个：

> **先问企业哪一步最贵、最慢、最依赖专家经验，再用 AI 去压缩这一步。**

# FitGround

## AI Fit Correction Copilot for Technical Designers

### 一句话定位

> **FitGround 帮助服装技术设计师在样衣出现 fit 问题后，基于人体尺寸、服装尺寸和当前试穿视觉证据，判断问题原因，并推荐下一版最值得尝试的修改方案，目标是提高下一版样衣一次改对的概率。**

这就是整个项目。

不是做 VTO。
不是做消费者推荐。
不是做完整 sizing platform。
不是做一个“懂服装”的聊天机器人。

只解决一个企业问题：

样衣出了问题，下一版到底怎么改？\boxed{\text{样衣出了问题，下一版到底怎么改？}}

------

# 1. 企业真正的痛点是什么

一个技术设计师拿到第一版样衣，发现：

```text
胸部有拉扯
腋下有斜向 drag line
袖长略长
肩部看起来正常
```

现在最耗时间的不是发现“它不合身”。

而是下一步：

```text
到底是胸围不够？
还是肩宽有问题？
还是袖窿结构导致的？
应该改 +1cm、+2cm 还是 +3cm？
这样改完会不会把别的地方改坏？
```

传统工作流通常是：

```text
Fit session
↓
Technical Designer 人工判断
↓
写 fit comments
↓
Pattern / garment modification
↓
重新打样
↓
再次试穿
↓
发现没完全解决
↓
再修改
```

真正昂贵的是：

> **不断依赖专家经验进行 trial-and-error。**

这个流程有四个企业痛点：

1. **专家知识高度依赖个人经验**
   同一个 fit symptom，不同技术设计师可能给出不同 correction。
2. **修改结果无法提前知道**
   `Bust +3cm` 做出去之前，并不知道下一版到底改善多少、有无副作用。
3. **实体迭代慢且贵**
   每一次错误 correction 都意味着重新改版、打样、运输、fit review。
4. **Fit knowledge 无法规模化**
   很多知识存在于邮件、fit comments、人的脑子里，不能直接变成 AI 可复用的 decision intelligence。

这才是 FitGround 要解决的问题。

------

# 2. 产品不是“判断 tight / loose”

如果 FitGround 只输出：

```text
Chest = Tight
```

价值很低。

因为技术设计师大概率早就看出来了。

真正有价值的输出应该是：

```text
Primary issue
Chest restriction

Likely cause
Insufficient chest ease

Recommended correction
Bust circumference +2.5 ~ 3.0 cm

Expected next-sample outcome
Chest: Tight → Regular
Shoulder: unchanged
Waist: unchanged

Alternative
Bust +2 cm
Residual chest tension likely

Risk
Low probability of over-correction

Confidence
0.87
```

客户真正购买的是：

> **Decision Support**

而不是 classification。

------

# 3. 真实产品场景

假设 Alvanon 的客户是一家服装品牌。

Technical Designer 正在审核一件 structured blazer。

已有信息：

### Body

```text
Bust       92 cm
Waist      74 cm
Hip        96 cm
Shoulder   39 cm
```

### Garment

```text
Bust       94 cm
Waist      82 cm
Shoulder   40 cm
Sleeve     59 cm
```

### Material

```text
Low-stretch woven
```

### Fit intent

```text
Regular structured fit
```

### 当前样衣视觉

模型能看到：

```text
horizontal chest tension
button pulling
diagonal drag near armhole
normal shoulder position
```

Technical Designer 现在真正的问题是：

> “下一版到底怎么改？”

FitGround 可以比较：

```text
Candidate A
Bust +1 cm

Candidate B
Bust +3 cm

Candidate C
Shoulder +1 cm

Candidate D
Sleeve -1 cm
```

系统预测：

| Correction    | Chest          | Shoulder       | Side Effect | Success |
| ------------- | -------------- | -------------- | ----------- | ------- |
| Bust +1cm     | Slightly tight | Normal         | Low         | 47%     |
| **Bust +3cm** | **Regular**    | **Normal**     | **Low**     | **89%** |
| Shoulder +1cm | Tight          | Slightly loose | Medium      | 31%     |
| Sleeve -1cm   | Tight          | Normal         | Low         | 8%      |

最终推荐：

> **Bust +3 cm**

这就是一个企业一眼能理解价值的 AI 系统。

------

# 4. FitGround 的核心 AI 链路

整个 AI 系统只做四步：

```text
Body / Garment / Visual / Material / Fit Intent
                        ↓
              ① Multimodal Understanding
                        ↓
              ② Physical Diagnosis
                        ↓
          ③ Modification Outcome Prediction
                        ↓
              ④ Correction Selection
```

数学上可以写成：

s=(I,B,G,M,F)s=(I,B,G,M,F)

其中：

- II：当前 fit 图片 / 3D 状态
- BB：body measurements
- GG：garment measurements / geometry
- MM：material / garment metadata
- FF：fit intent

对于候选修改：

a=ΔGa=\Delta G

模型预测：

s^′=Tθ(s,a)\hat{s}'=T_\theta(s,a)

然后从所有候选中选择：

a∗=arg⁡max⁡aU(s^′,a)a^*= \arg\max_a U(\hat{s}',a)

Utility 考虑：

U=−Fit Error−λ1Edit Magnitude−λ2Side EffectsU= -\text{Fit Error} -\lambda_1\text{Edit Magnitude} -\lambda_2\text{Side Effects}

也就是：

> **达到目标 fit + 尽量少改 + 不把其他地方搞坏。**

------

# 5. 为什么这里真的需要多模态大模型

这是项目必须守住的地方。

如果：

```text
Body bust = 92
Garment bust = 94
```

就能决定一切，那根本不需要 VLM。

一个规则系统就够了。

真正的服装 fit 不是这样。

同样：

Ease=+2cmEase=+2cm

在不同 garment 下意义不同：

```text
Stretch T-shirt
Structured blazer
Down jacket
Silk dress
```

同样看到 chest tension，也可能来自：

```text
Bust insufficient
Shoulder too narrow
Upper-chest geometry
Armhole geometry
Fabric stiffness
```

所以必须联合：

Visual+Measurements+GarmentStructure+Material+FitIntent\boxed{ Visual + Measurements + Garment Structure + Material + Fit Intent }

这就是 MLLM 的合理性。

------

# 6. FitGround 最强的地方：不是直接猜 correction

不要训练：

```text
Image → Bust +3cm
```

这太黑盒。

真正应该训练的是：

> **如果这么改，会发生什么？**

即：

(s,a)→s^′\boxed{ (s,a)\rightarrow\hat{s}' }

我会把这个模型叫：

## Multimodal Fit Transition Model

例如：

```text
Current:
Chest      Tight
Shoulder   Regular
Sleeve     Regular
```

输入：

```text
Candidate:
Bust +3cm
```

模型预测：

```text
Next:
Chest      Regular
Shoulder   Regular
Sleeve     Regular
```

换一个：

```text
Candidate:
Shoulder +2cm
```

预测：

```text
Chest      Slightly Tight
Shoulder   Loose
Sleeve     Regular
```

最后才选：

```text
Bust +3cm
```

这样既符合 technical designer 的思维方式，也方便做错误分析和验证。

------

# 7. Physical Diagnosis 怎么处理

保留，但不要做成一个庞大的“疾病分类系统”。

例如模型可以给：

```text
Likely cause:
Insufficient chest ease

Evidence:
- horizontal chest tension
- button pulling
- low-stretch woven material
- small bust ease
```

但不要假装：

> `insufficient chest ease` 是绝对 ground truth。

更合理的是：

> **Causal hypothesis**

然后通过修改后的结果验证它。

例如模型认为：

```text
Cause = insufficient bust ease
```

那么应该预测：

```text
Bust +1 → slight improvement
Bust +2 → more improvement
Bust +3 → target fit
Shoulder +1 → limited effect
```

如果 simulator 真产生类似结果，那么 diagnosis 才获得支持。

所以：

Diagnosis credibility=Intervention predictive validity\boxed{ Diagnosis\ credibility = Intervention\ predictive\ validity }

这个逻辑既技术硬，又不造假。

------

# 8. 数据怎么做

## A. FIT-Clean

你已经有：

```text
FIT-Clean v0.1
105,000 samples
```

它主要用于：

- 学真实 body / garment 分布；
- visual fit representation；
- baseline；
- multimodal warm-up；
- observational analysis。

但它不能直接告诉：

> “Bust +3cm 后发生什么”。

------

## B. FitGround Correction Dataset

真正核心资产。

利用：

```text
GarmentCode
+
Physics Simulation
```

为一个当前状态生成多个 candidate correction。

例如：

```text
Current State
│
├── Bust +1
│     └── outcome
│
├── Bust +2
│     └── outcome
│
├── Bust +3
│     └── outcome ← best
│
├── Shoulder +1
│     └── outcome
│
├── Shoulder +2
│     └── outcome
│
└── Sleeve -1
      └── outcome
```

我会把这个正式叫：

## Counterfactual Fit Correction Lattice

每个 case 保存：

```text
Current image / render
Body measurements
Garment measurements
Material
Garment type
Fit intent

Candidate modification
Intended modification
Realized modification

Simulated next state
Affected regions
Side effects

Utility
Best candidate
```

这一个数据结构可以同时支持：

```text
Forward prediction
Decision training
Preference construction
RLVR
Evaluation
```

------

# 9. 必须刻意做“MLLM 必要性”的难例

这是整个项目非常关键的一层。

不能随机生成数据以后就算完。

必须专门制造：

### Same measurements, different visual problem

```text
Body bust 92
Garment bust 94

Case A → Bust correction
Case B → Shoulder correction
```

### Same visual symptom, different cause

```text
Chest tension

Case A → Bust insufficient
Case B → Shoulder restriction
```

### Same ease, different material

```text
Ease +2cm

Stretch knit → acceptable
Rigid woven → restrictive
```

### Similar garment, different fit intent

```text
Oversized intent
vs
Regular intent
```

这部分可以叫：

## Visual-Disambiguation Set

它必须做到：

> **只看 measurement 做不好。**

否则整个 MLLM 故事不成立。

------

# 10. 模型方案

为了应聘，模型设计要体现能力，但不能堆技术。

### Baseline 1：Rule

```text
Ease heuristic
```

目的：

> 最简单规则能做到多少？

### Baseline 2：XGBoost / MLP

输入：

```text
body measurements
garment measurements
material metadata
```

这是一个非常重要的 baseline。

如果它已经很好，必须承认。

### Baseline 3：Base MLLM

输入全部模态。

不训练。

测试 foundation model 本身能力。

### Model 4：Counterfactual SFT

核心训练：

(s,a)→s′(s,a)\rightarrow s'

让模型学习：

> 修改 → 后果

再训练：

s→a∗s\rightarrow a^*

### Model 5：Physics-Verified RLVR

只有 SFT 已经有效之后再做。

不是为了简历写 RL。

------

# 11. Physics Simulation 在产品里到底是什么

不是“我们做了个 3D 衣服系统”。

它主要承担两件事。

### 离线

产生：

```text
Before
→ Modification
→ After
```

训练数据。

### 验证

模型说：

```text
Bust +3cm
```

Simulator 验证它是否：

```text
达到目标 fit
没有明显副作用
```

所以它是：

> **Physics-based simulated verifier**

不要声称：

> real-world ground truth。

这个边界一定要专业。

------

# 12. Post-training 路线

FitGround 可以成为非常好的 **MLLM Post-training 项目**。

但顺序必须是：

```text
Base MLLM
   ↓
Counterfactual SFT
   ↓
Decision SFT
   ↓
Physics-Verified RLVR
   ↑
只有真的有必要才做
```

不是：

```text
为了简历
→ LoRA
→ DPO
→ GRPO
→ RLVR
```

技术必须解决实际问题。

------

# 13. RLVR 到底在优化什么

模型选择：

a∼πθ(a∣s)a\sim\pi_\theta(a|s)

Simulator / cached counterfactual outcome 给出：

s′=Tsim(s,a)s'=T_{sim}(s,a)

Reward：

R=−Rfit-error−λ1Cedit−λ2Rside-effectR= -R_{\text{fit-error}} -\lambda_1 C_{\text{edit}} -\lambda_2 R_{\text{side-effect}}

模型逐渐学会：

> **不要只把问题“改没”，还要少改，并避免制造新的问题。**

这个 RLVR 才真正有企业意义。

------

# 14. 企业指标

不要用论文 Accuracy 做核心 KPI。

最重要的是：

## Simulation-Verified First-Pass Correction Rate

FPCR=#首选 correction 达到目标 fit#correction cases\boxed{ FPCR= \frac{ \#\text{首选 correction 达到目标 fit} }{ \#\text{correction cases} } }

它回答：

> **AI 的第一建议，有多少次可以一次改对？**

另外三个指标即可：

### Intervention Regret

U(a∗)−U(a^)U(a^*)-U(\hat a)

模型距离 simulator oracle 最优方案多远。

### Side-Effect Rate

修正一个地方之后，把原来正常部位搞坏的概率。

### Correction Magnitude Error

比如：

```text
Oracle: Bust +3cm
Model:  Bust +4cm
```

误差：

```text
1cm
```

技术设计师非常容易理解。

------

# 15. 最重要的实验

我不会把 Hero Experiment 做成普通 test set。

而应该是：

## Visual-Disambiguation Test

例如：

| Model              | Normal | Ambiguous Cases |
| ------------------ | ------ | --------------- |
| Rule               | 60     | 31              |
| XGBoost            | 73     | 38              |
| MLLM - Vision      | 75     | 41              |
| Base MLLM          | 79     | 61              |
| Counterfactual SFT | **87** | **80**          |

如果结果接近这种结构，你展示出来的能力非常强：

> **不是“MLLM 比 XGBoost 高几个点”，而是只有理解 visual fit evidence 后，才能区分 measurement 相似但 correction 不同的情况。**

这是招聘官很容易理解的。

------

# 16. 产品界面应该是什么样

不要做成聊天机器人。

Technical Designer 打开一个 Case：

```text
STYLE 24781 — FIT REVIEW
```

左侧：

```text
Body avatar
Current sample / 3D render
```

中间：

```text
Chest     HIGH
Shoulder  NORMAL
Sleeve    MEDIUM
```

右侧：

```text
Likely Cause
Insufficient chest ease

Recommended Correction
Bust +3cm

Expected Outcome
Chest   Tight → Regular
Waist   Regular → Regular
Shoulder Regular → Regular

Confidence 87%
```

下面可以展开：

```text
Alternative Corrections

Bust +2
Bust +3
Shoulder +1
...
```

查看 predicted consequence。

这才像真正的企业 AI 产品。

------

# 17. FitGround 明确不做什么

为了防止再次膨胀，我会直接冻结：

**不做：**

- Consumer size recommendation
- VTO 产品
- Return prediction
- Merchandising
- Inventory allocation
- Agentic commerce
- PIM
- 全球 body population sizing
- 整套 digital fashion platform

这些都可以写：

> future downstream applications

但不是项目。

------

# 18. 你真正展示给招聘官的能力

这个项目最有价值的是它可以同时证明你不是只会调用 API。

### AI / MLLM

你能做：

- multimodal input design
- VLM/MLLM
- structured numerical grounding
- multimodal reasoning

### Post-training

你能做：

- supervised data construction
- Counterfactual SFT
- Decision SFT
- preference/reward design
- RLVR

### Data

你能做：

- 100K+ dataset pipeline
- controlled synthetic data
- provenance
- leakage audit
- counterfactual data design

### Simulation

你能做：

- GarmentCode
- physical cloth simulation
- counterfactual generation
- verifier integration

### Evaluation

你能做：

- serious baselines
- ablation
- adversarial/ambiguous split
- business KPI
- oracle/regret evaluation

### Product

你能从：

```text
企业痛点
↓
AI任务
↓
数据
↓
模型
↓
验证
↓
产品
↓
商业指标
```

走完整闭环。

这一点对 AI Engineer / Applied AI / FDE 岗位尤其重要。

------

# 19. 最终项目定义

我建议正式锁死：

## FitGround

### AI-Powered Multimodal Fit Correction for Technical Designers

**Business problem**

> Technical designers still rely heavily on expert judgement and repeated physical sampling to determine how a garment should be corrected after fit issues are found.

**Solution**

> FitGround combines body measurements, garment data and visual fit evidence to diagnose likely fit causes, predict the outcome of candidate garment modifications, and recommend the smallest correction most likely to make the next sample fit correctly.

**Core AI**

MLLM+Counterfactual SFT+Fit Transition Modeling+Physics Verification+RLVR when justified\boxed{ \text{MLLM} + \text{Counterfactual SFT} + \text{Fit Transition Modeling} + \text{Physics Verification} + \text{RLVR when justified} }

**North Star**

Simulation-Verified First-Pass Correction Rate\boxed{ \text{Simulation-Verified First-Pass Correction Rate} }

**Business value**

> **Increase the probability that the next sample gets the fit right.**

这才是我会建议你拿去应聘的 FitGround：**先有真实商业痛点，再用足够硬的 AI 技术解决它；技术不是装饰，但项目也绝不被论文问题牵着走。**