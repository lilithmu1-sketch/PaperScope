# PaperScope 投稿复现说明

版本：paperscope-1.0-frozen；方向：read。原创代码MIT，论文材料按自身CC BY 4.0，见materials/sources.json。

## 环境与调用

本次执行宿主为Codex desktop独立实验子代理，实际原生日志报告gpt-6.1-sol、medium。Windows本地准备及校验使用Python 3.13；PDF转换使用pypdf 6.10.0，转换件和PDF原件均已随包提供。机械检查只需Python标准库，不要求安装PDF库。

在submission根目录执行：

```powershell
python tools/paperscope.py check-corpus materials/corpus/crabnet.json
python tools/paperscope.py check-claims --corpus materials/corpus/crabnet.json --claims runs/R01/claims.json --comparison runs/R01/comparison.csv
```

其余A运行同样检查。B须同时传入matbench-discovery.json与matbench-correction.json两个--corpus；C使用crabnet-incomplete.json。检查通过不等于引用在语义上充分支持结论，也不生成赛事分数。

## 新会话复跑

1. 准备与本次一致、可合法使用的宿主和模型档位；无法取得底层快照、seed或费用时如实说明。
2. 使用完全新上下文，禁用本次任务的跨会话记忆、外部检索、其他答案与评价表。输入清单见manifest各案例。
3. 将对应cases/*-task.txt全文作为任务，提供该案例materials输入。with条件加载skill/SKILL.md及其引用文件；without不加载Skill，其他任务要求与权限相同。
4. 不将cases/acceptance.md提供给执行模型；它是运行前评价标准，不是答案提示。
5. 每轮上限900秒、20次工具调用、12,000生成输出token；本宿主只能指令约束并事后审计，不能声称硬截断。不得人工续写/修正原始结果后冒充模型输出。保留新会话真实记录及失败。
6. 产生answer.md、claims.json、comparison.csv；机械检查另存。再用同一标准审阅，与原始输出分开。

C的输入是明示构造的删减文本，故不附全文PDF给模型；不能用包内完整A论文替C补材料。C转换件source_sha256指规范化块数组的哈希，实际提供文件的字节哈希另在冻结清单/官方ZIP清单中，二者含义不同。

## 证据入口

- report.md：实际结论、八轮汇总、失败和限制。
- manifest.json：每个案例素材、任务、标准和每次真实运行。
- review.json：由官方工具生成的原文索引。
- runs/*/：未改写原始答案、可见会话导出与来源哈希、真实时长、token计数、机械检查。
- evaluation/results/：开发AI同源、组别可见的逐项审阅；不是独立人工评审或官方分数。
- experiments/：冻结配置与历史哈希清单；原项目输入路径在投稿材料中映射，见manifest。

## 成本和人工参与

费用无法从宿主记录取得，不能填零。Token是日志报告值，不按价格反推费用。人类用户授权项目和独立子代理；开发AI准备素材/代码/协议、导出日志和评价，未人工补做子代理声明完成的阅读核心步骤。不存在已完成的独立人类专家审阅或非作者复现。

复制可见记录时省略系统/开发者隐私内容、隐藏思考和账号元数据；工具调用/返回均来自真实日志，不重造。原生源文件哈希与省略范围见每轮provenance.json，分享导出以export提交。

## 当前边界

本作品证明本次流程可检查并提供真实运行证据。A强基线与Skill均完整覆盖12项必要信息，没有观察到覆盖增益；B/C及正常复测只支持声明案例。不保证普遍优越或官方满分，独立最高档复核由评审安排。
