# AI论文阅读的证据核查：一次没有观察到Skill增益的对照

## 问题与方法

面对CrabNet“28个基准中几乎全部达到或超过最佳实践”的摘要，读者真正要判断的是：论文条件是否足以支持直接用于未见化学体系筛选？只生成流畅摘要可能漏掉比较对象、划分、输入信息和证据边界。

PaperScope Skill组织四项核查：将判断拆成可核查主张；回到连续原文与页序；对照数据/输入/指标/基线及调参条件；区分事实、推断和未知。代码只验证来源及引文存在性，语义支持仍单独审阅。这一取舍允许发现真实数字与错误结论并存的情况，而不把机械通过率冒充科学正确率。

本离线文章只讨论第一组A（R01无Skill、R02有Skill），不依据未包含的其他案例宣传泛化。两次使用同一冻结任务、完整原文信息、模型gpt-6.1-sol/medium、基础工具及预算，独立无历史上下文；唯一处理差异是加载Skill及随附契约。基线同样要求准确、可追溯和不确定性，不故意弱化。

## 实际输出与核查

两份原始答案都认定不能由这些基准直接证明新化学体系筛选可靠，均识别28任务的10+18来源、五折/固定种子划分、去重和标签聚合、MAE尺度、Roost强基线、嵌入例外、验证集调参、Automatminer输入条件和不确定性边界。

例如，正文说Roost与CrabNet总体相近；图1的MP band gap为Roost 0.260、CrabNet 0.263，MP shear modulus中RF 12.777、CrabNet 12.787。它们足以限制“全部严格胜出”，但小差异没有构成显著性检验。钢屈服强度的正文GPa标记存在需要回查原始标签的疑问，两份答案均保留原文标法，不擅自纠正单位。

运行前定义的12项必要信息，两次均完整覆盖；开发AI按每项0/1/2审阅均为24/24。此处是必要信息覆盖审阅，不是所有断言的总体准确率，更不是官方得分。原始回答、结构化主张、比较表与逐项理由一并提供。

R01记录时长368.055秒、9次工具、输出8346 token；R02为392.889秒、11次工具、输出10175 token。该组有Skill更长、更耗操作，不能宣传提速。时长含共享宿主并发和工具开销，token不直接换算价格，货币费用不可取得。

## 有价值的失败与限制

初版检查器只接受短块号，模型使用了输入中呈现的source_id:block_id，导致引用匹配误报。v1.1只兼容精确来源前缀，统一用于两种条件；原始答案没有修改。这是检查器修复，不算Skill增益。

本组没有覆盖改善。合理解释是明确任务和强基线已经达到这12项标准的上限；不能由一个案例推广为所有Skill无效，也不能为了得到改善而降低基线。审阅由开发AI同模型家族完成、组别可见，没有独立人工科学专家验证；模型底层快照与seed不可锁定。未重新训练CrabNet或验证真实材料发现。

## 离线复现

本包提供忠实全文定位文本、关键原页图、实际共同任务、完整Skill、两份未截断核心输出、真实日志摘录及原生来源元数据。为避免重复计入文本容量，完整PDF保留于公开仓库，本包以合法原文片段/页图和全文文本支持核查；没有靠作者摘要替代原文或实际输出。

```sh
python tools/text_to_corpus.py materials/crabnet-原文定位.txt materials/crabnet-generated.json
python tools/paperscope.py check-claims --corpus materials/crabnet-generated.json --claims runs/R01/claims.json --comparison runs/R01/comparison.csv
python tools/paperscope.py check-claims --corpus materials/crabnet-generated.json --claims runs/R02/claims.json --comparison runs/R02/comparison.csv
```

新模型运行需在独立会话提供共同任务和原文材料，with加载skill/paperscope/SKILL.md及参考，without不加载Skill；两臂保持相同模型/工具/预算，禁止把逐项审阅表交给模型。保留真实记录，不修改原始答案来通过校验。不同宿主或模型须重新声明范围，不能冒充复现本模型结果。

## 来源与贡献

Wang、Kauwe、Murdock与Sparks，Compositionally restricted attention-based network for materials property predictions，npj Computational Materials 7,77 (2021)，DOI 10.1038/s41524-021-00545-1，CC BY 4.0。页图仅渲染原页，文字只做空白归一化，保留原始来源与哈希。

项目贡献是阅读流程、输出契约、证据工具及真实对照设计，不是CrabNet算法或科学结果。原创代码/文档MIT；论文权利不变。完整可见会话保留在更完整的仓库/Skill材料；这里的日志是带源哈希及位置的忠实摘录，不宣称未脱敏原生遥测。
