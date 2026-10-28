# 实验输出契约 v1

`answer.md`：直接结论、证据说明、适用条件、未知与后续阅读动作。引用主张 ID，如 `[C01]`。不预设问题必须得到肯定或否定答案。

`claims.json` 为一个 JSON 对象，包含 `schema_version: "1.0"`、`source_ids`（非空、不重复）与 `claims`（1—30 项）。每个主张必须有以下字段：

| 字段 | 类型 | 规则 |
|---|---|---|
| id | 字符串 | 唯一，如 C01 |
| statement | 字符串 | 一项可以核查的主张，保留条件 |
| kind | 枚举 | fact / inference / unknown |
| verdict | 枚举 | supported / contradicted / insufficient |
| evidence | 数组 | 每项含 source_id、block_id、quote |
| reasoning | 字符串 | 解释引用和判断的关系；unknown 时写缺口 |

`quote` 是对应 block 的连续原文，引文可按空白归一化匹配；不得更改数字、单位、否定词或拼接不连续句子。每项不超过 2000 字符。fact/inference 至少一条引用；unknown 可无引用但必须 verdict=insufficient。contradicted 表示引用反驳 statement，而不是支持它。未报告型结论也需要说明检查范围，不能从一个段落推出全文都没有。

`comparison.csv` 为 UTF-8，含列 `item,paper_setting,target_setting,comparability,evidence_ids`。comparability 取 comparable / mismatch / unknown / not_applicable。只填写实际相关的项目，未知字段不猜测；evidence_ids 用分号连接 claims ID。

`checks.json` 由项目检查工具生成，明确 `semantic_support_verified: false`；人工语义核验另存评价记录，不覆盖原始输出。

实验输出不能包含参考核查表、预设答案、未经执行的检查结果或虚构成本。

