# 统一记录：一次撰写，多处引用

用于需要主张、比较和审计输出的任务。科学内容先来自阅读；此结构减少重复填写，不替代科学推理。仅需自然语言答复时无需采用。原claims/1.0输出继续兼容旧编译器。

## 草稿字段

顶层`schema_version`为`paperscope-review/1.0`，`source_ids`为实际语料ID列表。

- `claims`：沿用原claims的id、statement、kind、verdict、reasoning、evidence；id用C01等。evidence只含真实source_id、block_id及可选Unicode span，quote由程序复制。未知主张应kind=unknown、verdict=insufficient，注明缺口。
- `numbers`：可省略。每个记录含id（N01等）、value、units、conditions、basis（source/calculation/unverified）、source_locator、verification、evidence_ids及可选attachment_ids。文本字段均为非空字符串；source类型须连到有原文证据的claim。calculation类型还须formula；程序不执行公式、不认证计算，执行过的脚本/输入另列附件。没有单位/核验结果时明确写未知或待核验。
- `answer`：可选title及非空sections数组；每节可有heading，paragraphs为非空文本数组。可包含Markdown表格文本，不要求固定章节数量。
- `comparisons`：实际相关项目数组，各含item、paper_setting、target_setting、comparability、evidence_ids（claim ID数组）。状态为comparable/mismatch/unknown/not_applicable，未确定的实际条件保留unknown；本入口需要至少一行，纯阅读无比较任务改用自然语言或原契约，不编造比较。
- `attachments`：可省略。各含id（A01等）、path及purpose。path相对草稿所在目录，指向已经存在的真实文件。拒绝绝对路径、上级跳转、越界软链接、缺文件、重复ID；程序只复制数据，不执行附件代码。

数字id和claim id分别唯一。不在每个视图重复填数值：在数字表填一次value，其他位置使用模板；原始引文本身的数字仍保持原样。书写公式需清楚标明括号与单位，文本中出现相同数字并不证明它属于同一指标。

## 模板

| 写法 | 展开内容 |
| --- | --- |
| `{{C01}}` | C01的陈述及`[C01]`引用 |
| `{{C01.statement}}` / `{{C01.reasoning}}` | 陈述/理由原文 |
| `{{C01.ref}}` | `[C01]` |
| `{{N01}}` / `{{N01.value}}` | 数值表中value，不自动推断单位 |
| `{{N01.units}}` | 登记单位 |

claim的statement/reasoning仅能引用数字模板；答案和比较表能引用数字与claim。未知ID、非法字段及未展开模板会报错，避免把占位符误当结果。数字表使用实际读数或计算结果，不含模板；数字还需在文字中正确绑定指标和条件，这部分不能靠替换程序自动证明。

例如陈述可以写`在文中条件下，指标为{{N01}} {{N01.units}}。`，答案直接引用`{{C01}}`。这只是写法示例，不是任何论文的实际结果。语料块和数值必须来自本次材料；不要把示例当证据。

## 交付与复现

附件ID必须是A加数字，如A01；描述性名称放在purpose。可在正式装配前只读检查ID、路径和数字表中的附件引用：`python -B -X utf8 SKILL_DIR/scripts/assemble_review.py check-attachments --draft WORK/review-draft.json`。检查一次列出附件字段问题，非法ID会说明具体位置/值及合法写法；不自动重命名或同步引用，不生成输出目录。它不检查引文语义、计算、渲染依赖完整性或所有草稿字段；check通过仍须build和verify，缺图等问题在build时检查。build也会先执行相同附件检查。

需要可复算数字或渲染依赖闭合时，继续阅读[计算与派生附件](replay.md)。calculation_id绑定的运算会实际重算；未绑定的formula仍只是注释。新版额外输出calculations.json与dependency-map.json，verify检查这些记录；历史包使用它自己携带的对应版本工具，不将旧包缺少新字段称为历史损坏。

建议工作目录为`WORK/imported/`、`WORK/figures/`和`WORK/review-draft.json`。附件可声明`imported/source.pdf`、`imported/ingest-provenance.json`、`figures/region.png`、渲染provenance及实际计算脚本/输入/结果。未提供的附件使build失败；缺少的科学材料应记未知，不填假路径。

build输出最终四视图、实际附件、语料、原始草稿及改写附件路径的replay-draft、装配/引文出处、checks、工具副本和manifest。原始草稿保留原字节；portable草稿仅调整附件路径，变更分别记录哈希。numeric-review中的verification明确标为阅读者记录，不是程序认证。checks的semantic_support_verified保持false。

`numeric_source_alignment_review_needed`列出未在关联引文中找到相同value字符串的source数字。这个检查只是字面提示：图像读数、格式或单位换算都可能让字符串不同；相同字符串也可能指向别的量，不能自动证明数值、单位或语义相符。它不参与科学评分，不会把待核验数字偷偷认证为正确。

`verify REPORT_DIR`核对manifest文件、拒绝未登记文件，重新装配并逐字节比较四个最终视图。它不执行附件或模型，也不需要PDF解析依赖。可在全新目录从包内replay-draft和corpora重新build。包中tools副本用于重放；只执行自己信任的代码。manifest为未签名本地清单，不能证明外部真实性或阻止人同时篡改清单与数据。

若中途磁盘写入失败可能留下未封口目录；没有有效manifest及通过verify，不声称交付包完整。保留失败目录、另用新目录，不覆盖结果来隐藏错误。不得把离线装配成功称作独立模型验证、人工科学审阅或稳定提效。
