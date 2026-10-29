# PaperScope：把论文判断带回原文的证据工作台

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
