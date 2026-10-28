# PaperScope：可核查的论文阅读 Skill

先看结果：在gpt-6.1-sol/medium上，两组有/无Skill对照对12项必要信息均完整覆盖，未观察到覆盖增益；不宣传未证实的提升。另完成一篇论文迁移、缺失证据初测/复测和正常复测，共8次真实独立运行。

核心能力是把论文结论、原文证据、比较条件和边界放在同一条可核查链上。适用于具体科研阅读/方法迁移问题，不把阅读实验说成重做材料模型实验。

- [完整技术分享：第一组公平对照及离线证据](articles/first-pair/README.md)
- [技术方法与取舍](docs/技术说明.md)
- [真实结果与限制](report.md)
- [复现说明](README-reproduction.md)
- [Skill](skill/SKILL.md)
- [逐项审阅与运行数据](evaluation/results/run-summary.csv)

基础检查仅需Python 3.11+标准库（实际测试3.13）：

```sh
python -m unittest discover -s tests -v
python tools/paperscope.py check-corpus materials/corpus/crabnet.json
python tools/paperscope.py check-claims --corpus materials/corpus/crabnet.json --claims runs/R01/claims.json --comparison runs/R01/comparison.csv
```

所有结论限于自选案例。语义审阅由同模型家族开发AI完成、组别可见，未经独立人类专家确认；底层快照/seed不可固定。单纯引用匹配不证明语义支持，也不产生官方分数。

原创代码/文档采用MIT；论文及勘误按自身CC BY 4.0使用，来源、版本、原始哈希及变换见materials/sources.json。官方比赛程序、账号信息和私有系统/隐藏思考未加入本仓库。
