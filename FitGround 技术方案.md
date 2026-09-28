# FitGround 技术方案

**FitGround: Measurement-Grounded Multimodal Garment Fit Understanding**

核心目标不是再做一个普通的虚拟试衣模型，而是回答一个更基础的问题：

> **多模态模型判断衣服“紧 / 合身 / 松”时，到底有没有真正理解人体尺寸与服装尺寸之间的关系？**

整个系统采用 **“真实数据 + 可控仿真 + 反事实评测 + 多模态模型 + Grounding 诊断”** 的技术路线。

------

## 1. 整体技术架构

```text
                 FitGround
                     │
     ┌───────────────┴────────────────┐
     │                                │
Observational Data              Controlled Data
FIT / FIT-Clean                 Counterfactual Generator
105K samples                    GarmentCode + Simulation
     │                                │
     ▼                                ▼
Measurement Parser              Controlled Fit Ladder
Body Measurements               TIGHT
Garment Measurements            REGULAR
Visual Assets                   LOOSE
     │                                │
     └───────────────┬────────────────┘
                     ▼
             FitGround Benchmark
                     │
        ┌────────────┼───────────────┐
        │            │               │
     Vision       Measurement      Multimodal
     Baseline      Baseline          Model
        │            │               │
        └────────────┴───────────────┘
                     ▼
            Grounding Evaluation
                     │
        ┌────────────┼───────────────┐
        │            │               │
 Prediction      Sensitivity      Leakage
 Accuracy        / Causality       Detection
        │            │               │
        └────────────┴───────────────┘
                     ▼
              FitGround Score
```

------

# 2. 数据层

项目有两套数据，不把所有研究押在一个数据集上。

### A. FIT-Clean：真实观察数据

上游来自 FIT / FitVTO-100K，清洗后形成：

```text
FIT-Clean v0.1

Train: 100,000
Eval:    5,000
Total: 105,000
```

核心字段：

```python
body_height
body_bust
body_waist
body_hips

garment_bust
garment_length
garment_sleeve_length

person_image
cloth_image
target_image
```

进一步计算：

```python
bust_ease = garment_bust - body_bust

bust_ease_ratio = garment_bust / body_bust
```

因此模型不仅能看到图片，还能获得：

```text
人体尺寸
+
服装尺寸
+
人体－服装尺寸关系
+
最终穿着效果
```

### 为什么不能只使用 FIT？

我们已经发现：

```text
same person
+ same garment
+ different garment measurement
```

这种理想反事实结构在 FIT 中基本不存在。

也就是说：

> 衣服尺寸发生变化时，衣服本身往往也换了。

所以：

```text
服装外观变化
≈
服装尺寸变化
```

导致严重 confounding。

因此 FIT-Clean 主要承担：

> **observational training / statistics / baseline**

而不是最终因果评测。

------

# 3. Controlled Counterfactual Generator

这是 FitGround 最核心的技术模块。

采用：

```text
GarmentCode
+
NVIDIA Warp / cloth simulation
+
controlled rendering
```

生成真正的 **Controlled Fit Ladder**。

例如固定：

```text
Person A
Garment Design #03
Pose
Camera
Fabric
Texture
Seed
```

只改变：

```text
Sizing Condition
```

得到：

```text
        Same Body
           │
           ▼
   Same Garment Design
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
   TIGHT REGULAR LOOSE
```

最终形成：

```text
TIGHT
REGULAR
LOOSE
```

三个高度受控的 counterfactual examples。

------

# 4. 因果变量设计

FitGround 不简单声称：

```text
do(garment_bust = 90cm)
```

因为底层 GarmentCode 实际修改的是 sizing condition。

正式因果链定义为：

```text
Z → G → M → Y
```

其中：

### Z — Sizing Intervention

```text
TIGHT
REGULAR
LOOSE
```

### G — Garment Pattern Geometry

例如：

```text
pattern width
panel geometry
sleeve geometry
length
```

### M — Realized Garment Measurements

例如：

```text
garment_bust
garment_length
sleeve_length
ease
```

### Y — Final Fit

即：

```text
最终 drape
silhouette
wrinkle
tension
looseness
```

所以研究的核心不是简单相关性，而是：

> **当 Z 改变导致 G、M 和最终 Y 改变时，模型是否能够正确响应 M 与 Y 之间的变化。**

------

# 5. Controlled Fit Ladder

正式 Benchmark 的基本实验单元不是 image，而是：

```text
Fit Ladder
```

一个 ladder：

```text
Body B_i
Garment Design G_j

        ↓

TIGHT
REGULAR
LOOSE
```

当前 GPU E0：

```text
3 bodies
×
5 garment designs
=
15 ladders
```

每个 ladder：

```text
3 conditions
```

所以：

```text
15 × 3 = 45 controlled conditions
```

这是第一阶段实验。

后续验证成功后，再扩大到：

```text
hundreds / thousands of ladders
```

------

# 6. 两条视觉实验 Track

这是 FitGround 一个非常重要的设计。

## Track A — Measurement-Isolated

尽量去掉衣服尺寸本身产生的视觉提示。

输入：

```text
Canonical Garment Representation
+
Body Measurements
+
Garment Measurements
+
Target Fit Image
```

例如把 cloth representation：

```text
bbox normalize
canonical scale
canonical alignment
```

目标是尽可能让：

```text
cloth appearance
```

不能直接告诉模型：

```text
tight / loose
```

这样才能测试：

> 模型是不是真的用了 measurements。

------

## Track B — Naturalistic

保留真实服装视觉变化：

```text
size-specific garment image
+
measurement vector
+
target image
```

它更符合真实应用场景。

但它只能证明：

> 模型能够判断 fit。

不能单独证明：

> 模型真正使用 measurement reasoning。

所以：

```text
Track A = causal / diagnostic
Track B = realistic / application
```

------

# 7. 模型层

FitGround 不应该只比较一个 VLM。

建议形成四级 baseline。

## Level 1 — Measurement-only

最简单：

```text
body measurements
+
garment measurements
```

模型：

```text
Logistic Regression
XGBoost
MLP
```

输入：

```text
Δbust
Δwaist
Δhips
ease ratio
```

这是非常重要的 baseline。

------

# 8. Vision-only Baseline

输入：

```text
person
cloth
target
```

不提供 measurements。

可以测试：

> 单靠视觉能做到什么程度。

模型可以包括：

```text
CLIP
SigLIP
DINOv2
Vision Encoder + MLP
```

------

# 9. Multimodal VLM Baseline

输入：

```text
Person Image
Garment Image
Target Image
Measurements
Question / Task
```

模型可以测试：

```text
Qwen-VL
InternVL
LLaVA-family
Gemma multimodal
GPT-class VLM
```

输出例如：

```text
TIGHT
REGULAR
LOOSE
```

或者：

```text
fit score
```

------

# 10. Measurement-Grounded Model

FitGround 最终真正可以发展的模型方法不是简单：

```text
image → VLM
```

而是显式加入 **Measurement Encoder**。

架构：

```text
Person Image ───────► Vision Encoder ─────┐
                                          │
Garment Image ──────► Vision Encoder ─────┤
                                          │
Target Image ───────► Vision Encoder ─────┤
                                          ▼
                                     Fusion Layer
                                          ▲
Body Measurements ─┐                     │
                    ├─► Measurement Encoder
Garment Measurements┘                     │
                                          ▼
                                  Fit Reasoning Head
                                          │
                         ┌────────────────┼─────────────┐
                         ▼                ▼             ▼
                       Class           Score        Explanation
```

Measurement Encoder 可以首先采用：

```text
MLP
+
feature normalization
+
relative measurement encoding
```

输入不只是绝对值：

```python
body_bust
garment_bust
```

而更重要的是构造：

```python
delta_bust = garment_bust - body_bust
ratio_bust = garment_bust / body_bust
```

同样扩展到：

```text
waist
hip
length
sleeve
```

------

# 11. Measurement Relation Encoder

进一步可以设计成：

```text
Body Vector B
Garment Vector G

      │
      ▼
Relation Encoder
      │
      ├── absolute difference
      ├── ratio
      ├── normalized ease
      ├── interaction
      └── learned embedding
```

形式上：

R=f(B,G,B−G,G/B)R = f(B,G,B-G,G/B)

然后：

H=Fusion(Hvision,Hmeasurement,Hrelation)H = Fusion( H_{vision}, H_{measurement}, H_{relation} )

预测：

P(Y∣I,B,G,R)P(Y|I,B,G,R)

这就比简单把数字拼进 prompt 更像真正的 **measurement-grounded architecture**。

------

# 12. 关键评测不是 Accuracy

FitGround 最核心的创新点应该放在 **Grounding Evaluation**。

普通 benchmark 只问：

```text
预测对不对？
```

FitGround 还要问：

```text
为什么预测对？
```

------

## Metric 1 — Fit Accuracy

最基本：

```text
TIGHT / REGULAR / LOOSE
```

准确率。

------

## Metric 2 — Pairwise Ordering

一个 ladder 应满足：

```text
tightness(TIGHT)
>
tightness(REGULAR)
>
tightness(LOOSE)
```

或对应 looseness 反向排列。

------

## Metric 3 — Intervention Sensitivity

定义：

Δf=f(xloose)−f(xtight)\Delta f = f(x_{loose})-f(x_{tight})

检查模型预测是否随着 measurement intervention 正确变化。

------

# 13. Measurement Reliance

这是非常重要的一项。

分别运行：

### Full

```text
image + measurement
```

### Measurement Ablation

```text
image only
```

### Vision Ablation

```text
measurement only
```

比较：

Δmeasurement=Performancefull−Performancewithout−measurement\Delta_{measurement} = Performance_{full} - Performance_{without-measurement}

如果：

```text
有 measurements
≈
没有 measurements
```

那么即使模型 accuracy 很高，也可能根本没有使用 measurements。

------

# 14. Counterfactual Consistency

对于同一个 ladder：

```text
TIGHT → REGULAR → LOOSE
```

模型预测应该有连续一致变化。

例如：

```text
tight probability

0.83
 ↓
0.47
 ↓
0.11
```

而不是：

```text
0.81
0.79
0.82
```

后者说明模型基本没感知 intervention。

------

# 15. Leakage Detection

这是 Track A 必须做的。

因为即使进行了 canonical normalization，模型仍可能通过：

```text
silhouette width
cloth area
bbox ratio
sleeve proportion
length
```

猜到 size。

所以预先定义 D1–D16 visual descriptors。

然后训练：

```text
Multinomial Logistic Regression
```

预测：

```text
TIGHT
REGULAR
LOOSE
```

如果仅仅靠 cloth image 就能远高于：

```text
chance = 33.3%
```

则说明：

```text
Track A leakage
```

过强。

不能声称 measurement-isolated。

------

# 16. 人工验证

模型评测之前，先验证：

> 这些 TIGHT / REGULAR / LOOSE 在视觉上是否真的有意义。

采用 blind evaluation。

给评审：

```text
A
B
C
```

隐藏：

```text
condition label
measurement
metadata
```

评价：

```text
looseness
drape
wrinkle / tension
silhouette
length
sleeve
```

重点：

```text
LOOSE vs REGULAR
```

避免出现一种尴尬情况：

> 数字变化了，但人眼根本看不出衣服 fit 发生变化。

------

# 17. 统计分析

实验单位必须是：

```text
ladder
```

不能把三张图片当三个完全独立样本。

因此 bootstrap：

```text
10,000 bootstrap resamples
```

是在：

```text
ladder level
```

重新采样。

模型比较可以使用：

```text
paired bootstrap
Wilcoxon signed-rank
effect size
confidence interval
Holm correction
```

------

# 18. 工程技术栈

建议保持当前路线：

| 模块               | 技术                             |
| ------------------ | -------------------------------- |
| 主语言             | Python                           |
| Deep Learning      | PyTorch                          |
| 数据               | Pandas / PyArrow / Parquet       |
| Pattern Generation | **GarmentCode**                  |
| Cloth Simulation   | **NVIDIA Warp**                  |
| Rendering          | Blender / simulation renderer    |
| Image Processing   | OpenCV / Pillow                  |
| Vision Encoder     | CLIP / SigLIP / DINOv2           |
| VLM                | Qwen-VL / InternVL / LLaVA-class |
| Classical ML       | scikit-learn / XGBoost           |
| Experiment Config  | YAML                             |
| Artifact Tracking  | JSON / JSONL + SHA256            |
| Testing            | pytest                           |
| Versioning         | Git + frozen tags                |
| GPU                | RTX 3090 / 4090 24GB             |
| OS                 | Ubuntu 22.04                     |

------

# 19. 数据工程结构

推荐项目结构最终保持：

```text
FitGround/
│
├── data/
│   ├── raw/
│   ├── processed/
│   │   └── fit_clean_v0.1.parquet
│   ├── controlled/
│   └── manifests/
│
├── src/
│   ├── data/
│   ├── generation/
│   ├── simulation/
│   ├── measurement/
│   ├── models/
│   ├── evaluation/
│   └── leakage/
│
├── scripts/
│   ├── generate_controlled_ladders.py
│   ├── extract_measurements.py
│   ├── run_baselines.py
│   ├── run_vlm_eval.py
│   └── run_grounding_eval.py
│
├── configs/
│
├── artifacts/
│   ├── manifests/
│   ├── fingerprints/
│   └── hashes/
│
├── reports/
│   ├── runs/
│   ├── audits/
│   └── experiments/
│
├── tests/
│
└── docs/
```

------

# 20. 每次实验必须 Evidence-First

FitGround 的另一个工程原则是：

```text
Experiment
   ↓
Evidence
   ↓
Interpretation
   ↓
Decision
```

不是：

```text
Experiment
→ 看起来不错
→ 下一步
```

每个重要 Run 都留下：

```text
Question
Input
Config
Git SHA
Environment
Execution
Raw Result
Derived Result
Interpretation
Decision
Artifacts
SHA256
Next Step
```

这样最终论文中的每个数字都可以追溯到：

```text
dataset
→ manifest
→ code commit
→ config
→ run
→ result
```

------

# 21. 完整研究流水线

最终 FitGround 的技术路线可以浓缩成：

```text
FIT-100K
    ↓
Data Audit
    ↓
FIT-Clean 105K
    ↓
发现 observational confounding
    ↓
Controlled Counterfactual Generator
    ↓
GarmentCode + Warp
    ↓
Controlled Fit Ladders
    ↓
Track A / Track B
    ↓
Measurement-only baseline
Vision-only baseline
Multimodal baseline
Measurement-grounded model
    ↓
Accuracy
+
Counterfactual Consistency
+
Intervention Sensitivity
+
Measurement Reliance
+
Leakage Audit
    ↓
回答最终问题：

Does the model truly understand garment fit
through body–garment measurement relationships?
```

## 最终技术定位

如果要把 FitGround 技术方案压缩成一句话，我会定义为：

> **FitGround 是一个通过可控服装物理仿真、人体－服装测量关系建模和反事实干预评测，判断多模态模型是否真正具备 measurement-grounded garment fit reasoning 能力的研究框架。**

它的技术核心不是“再训练一个更大的 VLM”，而是三个东西：

Controlled Counterfactual Generation+Measurement-aware Modeling+Causal Grounding Evaluation\boxed{ \text{Controlled Counterfactual Generation} + \text{Measurement-aware Modeling} + \text{Causal Grounding Evaluation} }

这三个部分组合起来，才构成 FitGround 真正有论文价值的技术体系。







对，这应该直接成为 **FitGround 的核心产品原则**：

> **不是追求最高模型精度，而是在可接受成本下，把 fit 风险降到最低。**

老板真正关心的是：

Business Value=减少退货/返工/打样损失−AI与仿真成本\text{Business Value} = \text{减少退货/返工/打样损失} - \text{AI与仿真成本}

所以 FitGround 不应该每个 SKU 都上最贵的 VLM + 3D 仿真，而应该做成**分层决策系统**：

```text
Level 1：低成本规则 / Measurement Model
        ↓
置信度高 → 直接给结论
        ↓
不确定
Level 2：ML / Multimodal Model
        ↓
仍然高风险或不确定
Level 3：3D Simulation / VLM 深度分析
        ↓
极高价值 SKU / 高风险款
Level 4：人工技术设计师复核
```

比如：

| 方法                        | 成本 | 速度   | 适合场景           |
| --------------------------- | ---- | ------ | ------------------ |
| Measurement rules / XGBoost | 极低 | 毫秒级 | 大批量初筛         |
| Multimodal model            | 中   | 秒级   | 较复杂 fit 判断    |
| Garment simulation          | 较高 | 分钟级 | 高风险款、重点 SKU |
| 人工 fit expert             | 很高 | 小时级 | 最终高价值决策     |

这样 FitGround 的核心就变成了：

> **用最便宜的方法解决容易的问题，把昂贵计算和人工资源留给真正困难、高风险、高价值的样本。**

甚至可以正式定义一个 **Cost-to-Risk-Reduction** 指标：

CRR=Expected Fit Loss ReductionComputation + Simulation + Human Cost\text{CRR} = \frac{\text{Expected Fit Loss Reduction}} {\text{Computation + Simulation + Human Cost}}

系统不是问：

> “哪个模型 accuracy 最高？”

而是问：

> **“多花这 1 美元计算成本，能减少多少预期退货、返工或样衣成本？”**

这就非常适合企业。

例如一个普通 SKU：

```text
Measurement model：
Fit risk = LOW
Confidence = 96%
Cost ≈ $0.001
→ STOP
```

另一个风险 SKU：

```text
Measurement model：
Confidence = 58%
↓
Multimodal analysis：
Chest risk = HIGH
↓
3D simulation：
确认胸围过紧
↓
建议 pattern +3.5 cm
```

虽然第二个 SKU 花了更多计算成本，但如果它可能生产 50,000 件，避免一次 sizing mistake 的价值远高于几十美元的计算费。

所以我会把 FitGround 再升级成：

> **FitGround = Cost-Aware Fit Intelligence System**

它解决的不只是：

> “这件衣服合不合身？”

而是：

> **“这个问题值不值得进一步分析？应该调用多贵的模型？什么时候值得做 3D 仿真？什么时候应该交给人工？”**

这样它就从一个 **VLM/研究项目**，真正变成一个企业决策系统：

Fit Quality+Confidence+Cost+Business Risk→Optimal Action\boxed{ \text{Fit Quality} + \text{Confidence} + \text{Cost} + \text{Business Risk} \rightarrow \text{Optimal Action} }

这其实比单纯做 VLM 后训练更有商业价值，也更符合 Alvanon 这种公司的实际需求。