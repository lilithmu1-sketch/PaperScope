# PaperScope：可追溯论文阅读与证据复现

从原始PDF出发，把论文图表、上下文、适用条件和判断组织为可核对的证据。工具版本与论文阅读Skill参赛作品（Attempt 62601）一致；各案例的实验范围分别说明。

- **[当前技术分享：完整保留Figure 3与图注，并离线重渲染](articles/evidence-reading/README.md)**：包含原PDF、完整13文件Skill、真实R37输入输出、失败/自修正、出处及干净目录重放入口。无需模型API即可核验已有图像；不声称单例证明普遍增益。
- [完整Skill](articles/evidence-reading/skill/SKILL.md) · [实际交付](articles/evidence-reading/runs/R37/说明.md) · [复现脚本](articles/evidence-reading/reproduce.py)

当前文章聚焦图表证据任务。Skill赛项完整咨询对照有独立范围，不把它的资源观察值套用到本图表任务；旧78分对应历史文章，不是本次新版成绩。

## 历史工作台与真实接入

+
检查一条AI论文解读时，同时看模型陈述、真实引文、完整上下文和适用条件；按来源定位，并导出带文件哈希的审阅备注。所有页面本地运行，无模型API或CDN依赖。

- [完整动手教程与可离线案例](articles/workbench-v2/README.md)：真实引文为什么仍能伴随错误结论；从检索、逐字校验到人工审阅。
- [玻尔CLI真实接入与离线复核](docs/玻尔接入与复核.md)：6次实际调用，空图谱与书目定位均保留真实结果。
- [V1完整真实结果](report.md)：8次独立运行；两组有/无Skill均覆盖12项必要信息，未观察到覆盖增益。
- [原始Skill](skill/SKILL.md)、[原始首组分享](articles/first-pair/README.md)、[复跑边界](README-reproduction.md)。

```sh
python tools/workbench.py audit --project . --out generated/review
python tools/workbench.py search --project . --source crabnet --query "CrabNet 划分 泛化"
python tools/workbench.py probes --project . --out generated/probes
python -m unittest discover -s tests -v
```

打开generated/review/workbench.html。页面可按运行和关键词过滤，展开原文块并记录自己的审阅；图表须核对原PDF。登记文件哈希和引用存在性不证明语义支持，页面明确保持未自动语义验证状态。

当前原始数据共8轮、140条主张、227次未去重引用。它们是条目数，不是正确率。V2增加工作台、检索、可复现工具盲区探针与完整教程，没有把旧实验改写成不存在的Skill增益。新增工具探针不是模型真实犯错，也不是正式模型复跑。

环境：Python3.11+标准库；实际验证Windows/Python3.13。原创代码和文档MIT；论文与勘误按自身CC BY4.0，来源及原始哈希见materials/sources.json。语义审阅由开发AI同家族、组别可见完成，未经独立人工专家确认。玻尔CLI接入及其实际覆盖边界见新增接入报告。

