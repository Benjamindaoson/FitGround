<p align="right">
  <b>中文</b> · <a href="./README_EN.md">English</a>
</p>

# FitGround

**样衣不对。下一版改什么、改几厘米、别的地方会不会坏？**

FitGround 不是试衣间，也不是聊天机器人。它是给 **技术设计师** 用的下一版修正引擎：改一个具名纸样参数，**测出**几何变化，再看布料–人体物理后果，最后用效用函数排出下一版该怎么改。证据不够时，系统会 **拒答**，而不是编一个厘米数。

[![GitHub](https://img.shields.io/badge/GitHub-Benjamindaoson%2FFitGround-111)](https://github.com/Benjamindaoson/FitGround)
[![Hugging Face](https://img.shields.io/badge/HuggingFace-jlai300%2FFitGround-ffcc00)](https://huggingface.co/datasets/jlai300/FitGround)

| 当前样衣 | 胸围 +3 cm 之后 |
| --- | --- |
| ![baseline](reports/figures/baseline_render_front.png) | ![bust+3](reports/figures/bust_plus_3cm_render_front.png) |

这两张图是静态人台上的 Warp 垂坠证据，**不是**虚拟试穿产品图。

---

## 目录

1. [我们到底要解决什么问题？](#我们到底要解决什么问题)
2. [怎么解决的？](#怎么解决的)
3. [六个不容易忘掉的结论](#六个不容易忘掉的结论)
4. [实验过程：从观测数据走到干预格子](#实验过程从观测数据走到干预格子)
5. [训练结论：学到了什么，什么不该学](#训练结论学到了什么什么不该学)
6. [有没有更好的方案？](#有没有更好的方案)
7. [完整统计图库](#完整统计图库)
8. [状态矩阵与数据索引](#状态矩阵与数据索引)
9. [怎么跑](#怎么跑)
10. [硬限制](#硬限制)

---

## 我们到底要解决什么问题？

发现“胸口紧”通常并不贵。贵的是 **下一刀往哪改**：

```text
当前样衣有问题
    → 原因是胸围余量、肩部锁死、袖长，还是面料太硬？
    → 下一版改 +1 / +2 / +3 cm？
    → 改完会不会把腰、袖拖坏？
    → 证据不够时，能不能拒答而不是乱给数字？
```

成衣开发里，技术设计师真正花钱的环节不是“看一眼合不合体”，而是 **打样循环**：改纸样 → 再打一件 → 再试。每一厘米都有面料、车缝和时间成本。现有工具几乎都停在“看起来怎样”，不停在“下一版改哪一厘米”。

市面上常见方案解决的是另一件事：

| 常见做法 | 它真正回答的问题 | 为什么不够 |
| --- | --- | --- |
| 虚拟试穿 / VTO | “这件衣服穿上好不好看？” | 不告诉你下一版纸样改哪一厘米 |
| VLM / RAG / Agent 评语 | “看起来有点紧” | 没有干预，没有实测 Δ，没有物理后果 |
| 历史样本回归 | “过去类似的衣服胸围差多少” | 相关不是因果；不能做反事实 |
| 直接上 MLLM + RLVR | “模型很新” | 在平凡几何上解析法已经是 0 误差，硬吹模型是犯规 |

FitGround 只回答一句：**下一版样衣应该改什么。**

---

## 怎么解决的？

一条工程–研究闭环，每一步都留下 artifact：

```text
纸样参数干预
  → 实测二维几何（after − before，禁止把 intended 抄进 realized）
  → Warp 布料/人体物理（静态 OBJ 人台）
  → clearance / contact 等合体指标
  → 反事实候选排序
  → 决策效用（目标误差 + 改动量 + 副作用 + 不确定度）
  → 技术设计师工作台
```

![系统闭环](reports/figures/01_system_architecture.png)

![干预流水线](reports/figures/02_intervention_pipeline.png)

Shirt 胸围由一个具名参数控制：

```text
shirt.width.v = 目标胸围厘米 / 人体胸围厘米
```

所以在 **平凡几何体制** 里，要把衣服胸围加大 3 cm，解析逆映射就是把 `width.v` 加上 `3 / body_bust`。这不是模型“学会了”，这是纸样定义。任何把 intended 抄进 realized 的训练，都会得到假的 0 误差——本仓库的测试会拒收这种行。

### 三个必须讲清楚的分层

不要把下面四句话混成一句“GarmentCode physics PASS”：

| 层 | 状态 | 含义 |
| --- | --- | --- |
| 参数化纸样几何 | **PASS** | Shirt 面板可序列化，厘米来自测量 |
| 合成人体物理 `SYNTHETIC_BODY_PHYSICS` | **PASS** | Warp XPBD vs 仓库内静态 OBJ，米→厘米对齐 |
| SMPL / SMPL-X 人体物理 | **HARD_BLOCKED_LICENSE** | 权重不在，没有盗版，流水线不停 |
| 真人验证 | **HARD_BLOCKED_LICENSE** | 需要许可资产与知情同意 |

---

## 六个不容易忘掉的结论

### 1. ±3 cm 纸样修改可以校准到亚厘米 / 毫米级

胸围由 `shirt.width.v = 目标厘米 / 人体胸围` 控制。在 −3…+3 cm 网格上，**实测** `realized_delta_cm` 与 intended 相差约 `1e-14` cm；+3 cm 三次重复完全一致。

![胸围校准](reports/figures/03_bust_calibration.png)
![intended vs realized](reports/figures/bust_intended_vs_realized.png)
![校准曲线](reports/figures/bust_calibration_curve.png)

袖长：早期用面板 **Y** 测量是错的（GarmentCode 沿 **X** 构造）。改测量定义后 ±2 cm MAE = 0。不能因为旧 bug 给袖长 NO-GO。

肩宽：Shirt **没有独立肩宽自由度**。`sleeve.connecting_width` 扫描：肩宽 Δ = 0 cm，袖长会被带动。正式结论：

`SHOULDER_ACTION = NO_GO_FOR_CURRENT_PATTERN_FAMILY`

副作用是结构性的，不是噪声。`flare=1` 时，±3 cm 胸围修改会 **100%** 带动腰围。决策效用必须给副作用定价，否则系统会永远推荐“改得最大的那一刀”。

![副作用](reports/figures/bust_side_effects.png)

### 2. 修正对真实布料–人体 clearance / contact 有可测影响

同一件 Shirt，静态人台、单位对齐之后：

| 版本 | 胸围 clearance p10 | contact ratio |
| --- | --- | --- |
| 当前样衣 | 0.47 cm | 0.027 |
| +1 cm | 0.48 cm | 0.029 |
| +2 cm | 0.48 cm | 0.027 |
| +3 cm | 0.50 cm | 0.022 |

变化是 **毫米级 clearance**，不是试衣大片。但对“改纸样有没有物理后果”这个问题，答案是有。

![物理前后](reports/figures/04_physics_before_after.png)
![clearance / contact](reports/figures/05_clearance_contact.png)
![physics_clearance_contact](reports/figures/physics_clearance_contact.png)

| 当前 | +1 cm | +2 cm | +3 cm |
| --- | --- | --- | --- |
| ![b0](reports/figures/baseline_render_front.png) | ![b1](reports/figures/bust_plus_1cm_render_front.png) | ![b2](reports/figures/bust_plus_2cm_render_front.png) | ![b3](reports/figures/bust_plus_3cm_render_front.png) |

同测量、不同面料弯曲（default vs stiff）——这是后面视觉必要性实验的物理原料：

| 紧身 default | 紧身 stiff | 宽松 default | 宽松 stiff |
| --- | --- | --- | --- |
| ![td](studio/public/evidence/tight_default_render_front.png) | ![ts](studio/public/evidence/tight_stiff_render_front.png) | ![rd](studio/public/evidence/roomy_default_render_front.png) | ![rs](studio/public/evidence/roomy_stiff_render_front.png) |

### 3. 简单几何体制不需要机器学习，解析法最好

| 方法 | 测试 MAE (cm) | 说明 |
| --- | --- | --- |
| 解析逆映射 | **~0** | `Δwidth = Δcm / body_bust` |
| Transition SFT MLP | 0.47 | 88 行格子，test n=16 |
| 观测 B0 均值余量 | 8.11 | FIT-Clean 104,999 行，**不是**干预 GT |
| B1 OLS | 8.08 | 人体四围长回归衣胸围 |
| B1 XGBoost | 7.88 | 同上；相关仍不是因果 |
| 纸样 Ridge | 3.45 | 192 张生成纸样图 |
| 纸样 CNN | 6.23 | RTX 4090，40 epoch，没有打过 Ridge |
| CNN+body | 6.24 | 没有多模态增益 |

![基线梯子](reports/figures/06_baseline_ladder.png)
![平凡 vs 复杂](reports/figures/09_trivial_vs_complex.png)
![观测 MAE](reports/figures/observational_baseline_mae.png)

把 intended 抄进 realized 会得到假的 0 误差。本项目禁止这样做。解析法赢，是因为这张 Shirt 胸围映射本来就是恒等几何，不是模型“很强”。

### 4. 材料/垂坠歧义里，视觉必要性还没被统计成立

构造 **33 对** 同规格、不同弯曲刚度的物理样本。其中 **7 对**（21%，bootstrap 95% CI 约 9%–36%）最优修正翻转。

分组切分上：measurement-only 准确率 0.90 [0.70, 1.00]，drape 特征 1.00；**CI 重叠** →

**`VISION_NECESSITY_NOT_ESTABLISHED`**

没有为了 MLLM 故事去调 split。纸样 Ridge 已经打过 CNN，这是同一条诚实原则。

![视觉消歧](reports/figures/07_visual_disambiguation.png)
![多模态消融](reports/figures/08_multimodal_ablation.png)

Qwen2-VL-2B-Instruct 零样本结构化 JSON：parse rate 100%，动作匹配 83%（n=12，多数类 `no_edit`）。数据太小，不做 LoRA，避免泄漏。匹配率接近多数类，不能写成“视觉模型已经会改纸样”。

### 5. OOD 时系统拒答，而不是乱给厘米

| 切分 | 结果 |
| --- | --- |
| IID 平凡几何 | 解析 MAE ~0（n=88） |
| 合成人体 OOD（mean_female / male） | 几何映射仍 ~0（n=402）；**禁止叫真人泛化** |
| 面料 OOD | 只用尺寸会与 stiff 金标分歧 21% [9%, 36%]（n=33） |
| 动作超出 ±3 cm | 策略：abstain |
| flare=1 时 ±3 cm 胸围 | 腰围 100% 跟随（结构性副作用，n=162） |

失败感知（n=633）：OOD 检测 AUROC **0.90**，拒答精确率 **1.0**。分桶里，OOD 人体 / OOD 面料 / 歧义样本全部拒答；分布内简单样本准确率 1.0、拒答率 0。Hero Case 4 明确展示 **AI 拒绝给修正**。

![OOD](reports/figures/10_ood_results.png)
![风险–覆盖](reports/figures/11_risk_coverage.png)
![决策后悔](reports/figures/12_decision_regret.png)
![失败分桶](reports/figures/14_failure_gallery.png)

### 6. 实验结果直接变成技术设计师的下一版建议

工作台问的是同一句话：**下一版样衣该改什么？** 页面右上角可以一键切换中 / 英。

```bash
cd studio && npm install && npm run dev
# http://127.0.0.1:43187
```

五个 Hero Case：胸围过紧 → +3 cm；同尺寸不同面料；腰围副作用让更小修改胜出；OOD 人台拒答；肩 vs 胸由证据裁定为肩宽 NO-GO。

![Hero cases](reports/figures/13_hero_cases.png)
![候选效用](reports/figures/candidate_utility_ranking.png)

---

## 实验过程：从观测数据走到干预格子

这条路不是“先训一个大模型再找故事”，而是反过来：**先证明干预能不能测出来，再决定学习有没有必要。**

### 第一步：观测数据告诉你相关，不告诉你下一刀

FIT-Clean 来自公开 FIT-100K 测量字段（约 10.5 万行，按人哈希切分）。它可以回答“历史上类似体型的衣服胸围差多少”，但不能构造反事实。B0 中位余量 MAE 8.11 cm，XGBoost 也只能到 7.88 cm——这是观测上限，不是修正系统的失败。

Eval 子集（FIT-Clean eval）人体与服装尺寸：

| 人体胸围 | 人体腰围 | 人体臀围 | 人体身高 |
| --- | --- | --- | --- |
| ![eb](reports/figures/eval_hist_body_bust_cm.png) | ![ew](reports/figures/eval_hist_body_waist_cm.png) | ![eh](reports/figures/eval_hist_body_hips_cm.png) | ![eht](reports/figures/eval_hist_body_height_cm.png) |

| 衣胸围 | 衣长 | 袖长 | 胸围余量 |
| --- | --- | --- | --- |
| ![gb](reports/figures/eval_hist_garment_bust_cm.png) | ![gl](reports/figures/eval_hist_garment_length_cm.png) | ![gs](reports/figures/eval_hist_garment_sleeve_cm.png) | ![ge](reports/figures/eval_hist_bust_ease_cm.png) |

| 余量比 | 余量比离散化 | 衣长/身高 | 余量散点 |
| --- | --- | --- | --- |
| ![er](reports/figures/eval_hist_bust_ease_ratio.png) | ![eq](reports/figures/eval_bust_ease_ratio_quantization.png) | ![elr](reports/figures/eval_hist_garment_length_height_ratio.png) | ![esc](reports/figures/eval_bust_ease_scatter.png) |

全量 FIT 分布审计（同一套字段，确认 eval 不是特例）：

| 人体胸围 | 人体腰围 | 人体臀围 | 人体身高 |
| --- | --- | --- | --- |
| ![fb](reports/figures/full_fit_hist_body_bust_cm.png) | ![fw](reports/figures/full_fit_hist_body_waist_cm.png) | ![fh](reports/figures/full_fit_hist_body_hips_cm.png) | ![fht](reports/figures/full_fit_hist_body_height_cm.png) |

| 衣胸围 | 衣长 | 袖长 | 胸围余量 |
| --- | --- | --- | --- |
| ![fgb](reports/figures/full_fit_hist_garment_bust_cm.png) | ![fgl](reports/figures/full_fit_hist_garment_length_cm.png) | ![fgs](reports/figures/full_fit_hist_garment_sleeve_cm.png) | ![fge](reports/figures/full_fit_hist_bust_ease_cm.png) |

| 余量比 | 衣长/身高 |
| --- | --- |
| ![fer](reports/figures/full_fit_hist_bust_ease_ratio.png) | ![felr](reports/figures/full_fit_hist_garment_length_height_ratio.png) |

数据工程本身也留下了痕迹：分片内存、近重复与泄漏审计都在 `reports/` 里。观测图像字节 **没有** 进本仓（许可与体积）；进仓的是测量字段、schema 和审计图。

![分片内存](reports/figures/memory_by_shard.png)

### 第二步：把纸样参数变成可重复的厘米

GPU 上（RTX 4090，Warp 1.0.0-beta.6，Torch 2.5.1+cu124）对 GarmentCode Shirt 做原子校准：改 `shirt.width.v`，序列化面板，**测量** after−before。得到恒等映射之后，才能谈格子、物理和学习。

早期袖长探针沿面板 Y 得到 Δ=0，这是测量定义错误，不是纸样坏了。肩宽探针证明当前家族没有独立肩宽自由度——这是 **NO-GO 结论**，不是没做完的实验。

### 第三步：把厘米再送进布料物理

人体 OBJ 是米，布料网格是厘米。对齐之后，Warp XPBD 在静态人台上给出 clearance / contact。v0.2 冻结：**636** 条转移（0 重复 state-action，0 条 intended→realized 抄袭），**127** 条物理仿真成功。视觉消歧另有 33 对 / 71 个物理样本。

没有 SMPL-X 权重。流水线没有停，而是打上 `SYNTHETIC_BODY_PHYSICS`，并禁止把合成人台写成真人验证。

### 第四步：只在学习可能赢过解析法的地方训练

平凡几何上解析法已经是 0。我们仍然训练了 Transition SFT、Decision SFT 和 RLVR——目的不是刷榜，而是 **量出学习还有没有残差**。答案：SFT 比解析法差；决策 holdout n=3 后悔已经是 0；RLVR 没有额外收益，正式 `NOT_JUSTIFIED`。

复杂体制（同测量、不同垂坠）里最优修正会翻转，但分组切分 CI 重叠，视觉必要性 **未统计成立**。这才是诚实的停止线。

---

## 训练结论：学到了什么，什么不该学

GPU 训练跑完了：B0、B1、B1-Ridge、B1-XGBoost、生成纸样 B2/B3、Transition SFT、Decision SFT、RLVR。FIT-100K 的 197GB 图像 **没有下载**；视觉基线用的是光栅化纸样图（192 张）。

| 任务 | 状态 | 头条数字 |
| --- | --- | --- |
| B0 余量启发式 | PASS | test MAE 8.11 cm（观测，非干预 GT） |
| B1 OLS | PASS | test MAE 8.08 cm |
| B1 Ridge | PASS | test MAE 8.08 cm |
| B1 XGBoost | PASS | test MAE 7.88 cm |
| B2 FIT-100K 视觉 | NOT_RUN | 图像不在磁盘 |
| B2 生成纸样 Ridge | PASS | test MAE 3.45 cm（192 张图） |
| B2 生成纸样 CNN | PASS | test MAE 6.23 cm；Ridge 赢 |
| B3 CNN+body | PASS | test MAE 6.24 cm；无多模态增益 |
| Transition SFT MLP | PASS | MAE 0.47 cm；解析法 ~0 |
| Decision SFT MLP | PASS | holdout 准确率 1.0，后悔 0.0（**n=3，不吹**） |
| RLVR REINFORCE | NOT_JUSTIFIED | 300 CUDA step，SFT 之后没有残差 |
| Qwen2-VL-2B 零样本 | PASS | parse 100%，match 83%，n=12，多数类 |

![Transition SFT MLP](reports/figures/transition_sft_mlp_loss.png)
![Transition SFT LM](reports/figures/transition_sft_lm_loss.png)
![Decision SFT](reports/figures/decision_sft_mlp_loss.png)
![RLVR](reports/figures/rlvr_reward.png)

**一句话训练结论：**

- 观测回归再强，也回答不了“下一版改几厘米”。
- 纸样图上线性模型打过小 CNN，说明这张图的信息几乎是可量测的几何，不是纹理玄学。
- 干预格子上，解析逆映射是铁基线；SFT 没有赢过它。
- RLVR 在后悔已经为 0、holdout 只有 3 条时没有研究价值。
- 视觉 / MLLM 只在「同测量导致不同最优修正」且「分组切分 CI 分离」时才有必要。当前未成立。

更完整的论证见 [`reports/WHEN_IS_LEARNING_NECESSARY.md`](reports/WHEN_IS_LEARNING_NECESSARY.md) 与 [`reports/TRAINING_RUN.md`](reports/TRAINING_RUN.md)。

---

## 有没有更好的方案？

有。我们故意没走那些“更好看”的路，原因如下。

| 看起来更强的方案 | 为什么这次不采用 / 什么时候才值得 |
| --- | --- |
| 一上来就微调 Qwen2-VL / GPT-4V | 平凡几何上解析法已经 0 误差；先证明学习有必要 |
| 用 Agent 自动改纸样 | 没有实测 Δ 和物理后果，只是会说话的试衣间 |
| RLVR / 强化学习改纸样 | 决策 holdout n=3，后悔已是 0；RLVR `NOT_JUSTIFIED` |
| 用 FIT-100K 图像硬训 CNN | 未下载 197GB；192 张纸样图上 Ridge > CNN |
| 把 intended 当 realized | 这是造假，测试会拒 |
| 没有 SMPL-X 就停工 | 错误。合成人台继续跑，并打上标签 |
| 为 Shirt 强行做肩宽 PASS | 没有独立自由度；NO-GO 比假 PASS 更有研究能力 |
| 调 split 让视觉必要性成立 | 7/33 翻转是真的；统计成立是假的。保留后者 |
| 把毫米级 clearance 写成生产 fit | 人台证据 ≠ 真人试衣 |

**更好的下一步（有许可之后）** 不是换一个更炫的模型名，而是：

1. 在许可的 SMPL-X 上重复同一套格子  
2. 把解析逆映射继续当平凡体制的铁基线  
3. 只有当同测量、不同真实垂坠导致最优修正翻转 **且** 分组切分 CI 分离时，才宣称视觉/MLLM 有必要  
4. 真人 fit session 做验证，而不是把合成人台叫生产系统  
5. 若要学复杂体制，先把物理金标和分组切分做大，再考虑 LoRA——不要从零样本 n=12 直接跳到“多模态成功”

---

## 完整统计图库

上面正文已经按结论插入了主图。下面是仓库里 **全部** 仍保留的统计图与证据图，按实验阶段归档，避免有图没进故事。

### A. 系统与干预

| 系统架构 | 干预流水线 | Hero cases |
| --- | --- | --- |
| ![a1](reports/figures/01_system_architecture.png) | ![a2](reports/figures/02_intervention_pipeline.png) | ![a3](reports/figures/13_hero_cases.png) |

### B. 几何校准

| 胸围校准 | intended vs realized | 校准曲线 | 副作用 |
| --- | --- | --- | --- |
| ![b1](reports/figures/03_bust_calibration.png) | ![b2](reports/figures/bust_intended_vs_realized.png) | ![b3](reports/figures/bust_calibration_curve.png) | ![b4](reports/figures/bust_side_effects.png) |

### C. 合成人体物理

| 物理前后 | clearance/contact | 物理指标 | 候选效用 |
| --- | --- | --- | --- |
| ![c1](reports/figures/04_physics_before_after.png) | ![c2](reports/figures/05_clearance_contact.png) | ![c3](reports/figures/physics_clearance_contact.png) | ![c4](reports/figures/candidate_utility_ranking.png) |

### D. 基线、视觉、OOD

| 基线梯子 | 视觉消歧 | 多模态消融 | 平凡 vs 复杂 |
| --- | --- | --- | --- |
| ![d1](reports/figures/06_baseline_ladder.png) | ![d2](reports/figures/07_visual_disambiguation.png) | ![d3](reports/figures/08_multimodal_ablation.png) | ![d4](reports/figures/09_trivial_vs_complex.png) |

| OOD | 风险–覆盖 | 决策后悔 | 失败分桶 |
| --- | --- | --- | --- |
| ![d5](reports/figures/10_ood_results.png) | ![d6](reports/figures/11_risk_coverage.png) | ![d7](reports/figures/12_decision_regret.png) | ![d8](reports/figures/14_failure_gallery.png) |

### E. 训练曲线（负结果也保留）

| Transition MLP | Transition LM | Decision SFT | RLVR |
| --- | --- | --- | --- |
| ![e1](reports/figures/transition_sft_mlp_loss.png) | ![e2](reports/figures/transition_sft_lm_loss.png) | ![e3](reports/figures/decision_sft_mlp_loss.png) | ![e4](reports/figures/rlvr_reward.png) |

| 观测 MAE | 分片内存 |
| --- | --- |
| ![e5](reports/figures/observational_baseline_mae.png) | ![e6](reports/figures/memory_by_shard.png) |

数字底稿：[`artifacts/FINAL_METRICS.json`](artifacts/FINAL_METRICS.json) · [`artifacts/FINAL_STATUS.json`](artifacts/FINAL_STATUS.json) · [`artifacts/hero/ood_results.json`](artifacts/hero/ood_results.json) · [`artifacts/hero/failure_aware.json`](artifacts/hero/failure_aware.json) · [`artifacts/hero/visual_disambiguation.json`](artifacts/hero/visual_disambiguation.json) · [`artifacts/training/observational_and_vision_baselines.json`](artifacts/training/observational_and_vision_baselines.json) · [`artifacts/hero/mllm_eval.json`](artifacts/hero/mllm_eval.json) · [`artifacts/hero/correction_lattice_v0.2.jsonl`](artifacts/hero/correction_lattice_v0.2.jsonl)

GPU 关机后未能进仓的东西写在 [`artifacts/GPU_SHUTDOWN_ASSET_INVENTORY.md`](artifacts/GPU_SHUTDOWN_ASSET_INVENTORY.md)：约 677 张纸样 PNG、大批 Warp `.obj`、以及 4.2GB 的 Qwen 权重大小。**结论和数字在 JSON 里，不在丢失的 PNG 里。**

---

## 状态矩阵与数据索引

只允许四种词：`PASS` · `NO_GO_WITH_EVIDENCE` · `NOT_JUSTIFIED` · `HARD_BLOCKED_LICENSE`

| 项目 | 状态 |
| --- | --- |
| Core / Warp / PyTorch | PASS |
| 参数化几何 / 合成物理 | PASS |
| 胸围 / 袖长 / 大格子 | PASS |
| 肩宽 | NO_GO_WITH_EVIDENCE |
| 视觉消歧实验 | PASS（结论：必要性未成立） |
| 经典 / 视觉 / 多模态基线 | PASS |
| 预训练 MLLM 实验 | PASS（零样本，n=12） |
| Transition | PASS（解析法更好） |
| Decision SFT | PASS（n=3，不吹） |
| RLVR | NOT_JUSTIFIED |
| OOD / 失败感知 / Demo | PASS |
| SMPL-X / 真人 | HARD_BLOCKED_LICENSE |

格子：636 条转移，0 重复 state-action，0 条把 intended 抄进 realized。物理仿真 127 条 SIMULATED。

文字报告：[`reports/EXPERIMENT_TABLE.md`](reports/EXPERIMENT_TABLE.md) · [`reports/WHEN_IS_LEARNING_NECESSARY.md`](reports/WHEN_IS_LEARNING_NECESSARY.md) · [`reports/TRAINING_RUN.md`](reports/TRAINING_RUN.md) · [`reports/OOD_REPORT.md`](reports/OOD_REPORT.md) · [`reports/FAILURE_ANALYSIS.md`](reports/FAILURE_ANALYSIS.md) · [`reports/RESUME_CLAIMS.md`](reports/RESUME_CLAIMS.md) · [`reports/TECHNICAL_ARCHITECTURE.md`](reports/TECHNICAL_ARCHITECTURE.md)

镜像：[GitHub](https://github.com/Benjamindaoson/FitGround) · [Hugging Face datasets](https://huggingface.co/datasets/jlai300/FitGround)

---

## 怎么跑

```bash
make smoke              # pytest
make benchmark-fast     # 基于已有 artifacts 收口
cd studio && npm install && npm run dev   # 工作台 :43187 ，页面内中/英切换
```

GPU（需要 GarmentCodeV2 + Warp + RTX；本云环境没有那台已欠费关机的 4090）：

```bash
source scripts/gpu/flux_env.sh
python scripts/gpu/hero_pipeline.py
python scripts/gpu/expand_visual_physics.py
python scripts/gpu/finalize_closure.py
```

---

## 硬限制

- 没有 SMPL-X 权重，没有真人验证。  
- 目前只有 Shirt / tee 家族。  
- v0.2 的 677 张纸样 PNG 和大批 `.obj` 留在已停机的 GPU 上，未进本仓；**数字在 JSON 里**。  
- Qwen2-VL 评测 n=12，匹配率接近多数类。  
- Decision / RLVR holdout 太小。  
- 物理 clearance 变化是毫米级人台结果，不是生产 fit session。

<p align="right">
  <b>中文</b> · <a href="./README_EN.md">English</a>
</p>
