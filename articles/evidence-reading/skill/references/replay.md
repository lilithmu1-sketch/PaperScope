# 计算与派生附件的便携复核

## 四则计算

在统一草稿中可添加calculations数组。每项含K开头的唯一id、operation（add/subtract/multiply/divide）、恰好两个operands，以及可选decimal_places（0—20）。操作数为十进制字符串、前面已算出的K ID，或`{"number_id":"N01"}`；后者引用非calculation类型数字的value，避免重复填源值。数字必须是普通十进制，不含千分符、百分号或单位；单位另填，不自动换算。

```json
[
  {"id":"K1","operation":"subtract","operands":[{"number_id":"N02"},{"number_id":"N01"}]},
  {"id":"K2","operation":"divide","operands":["K1",{"number_id":"N02"}]},
  {"id":"K3","operation":"multiply","operands":["K2","100"],"decimal_places":1}
]
```

这只是计算结构示例，不提供论文数据。目标numbers项标basis=calculation、calculation_id=K3，value填实际执行的结果，formula仍写可读公式。build将计算结果与该value按Decimal数值比较；不一致、除零、前向/循环引用会失败。输出calculations.json；verify重新计算并逐字节核对。50位十进制精度、ROUND_HALF_EVEN舍入；操作中间值也可能有有限精度误差。需其他舍入方式、统计分析、拟合或更高精度时使用实际可移植脚本和输入，并另行记录验证范围，不硬套此入口。

源值正确性、单位一致性、公式选择与自然语言formula和操作树是否相符仍须阅读者检查。只写formula而不绑定calculation_id仍是旧版注释，未执行；不可称所有数字已自动验证。不执行任意表达式或附件代码，也不会恢复模型或历史起草过程。

## 渲染附件

把render_region生成的provenance.json声明为附件，并声明原PDF。渲染工具须与记录的script_sha256一致：当前工具自动带入；历史版本不同则把实际旧脚本作为附件归档。程序按内容哈希定位该脚本，只复制、不执行历史代码。

保留provenance和region.png/context.png原目录关系。未单独登记的图将从出处所在目录收集，路径必须在草稿目录内，哈希必须匹配。不存在时直接失败；不能用另一张图替代或伪造出处。重复内容只需保存一份。dependency-map.json记录原出处到PDF、脚本及图像的便携路径映射，原出处字节保持不变；自动收集文件进入replay-draft附件列表，支持整包搬迁后再次build。

```sh
python -B -X utf8 REPORT/tools/assemble_review.py verify REPORT
python -B -X utf8 REPORT/tools/assemble_review.py replay-renders REPORT --out NEW_RENDER_DIR
```

verify只需标准库，检查声明渲染依赖的完整性，不是重渲染。replay-renders需pypdfium2和Pillow，使用包内当前可信工具、原PDF与记录参数，输出新目录，记录实际库版本，逐图比较PNG哈希。不同版本可能导致字节差异；返回3表示有图不一致，保留结果查因，不能掩盖或宣称成功。不能复原原环境时如实报告。没有渲染记录时计数0，不据此宣称完成图像复现。

此检查覆盖本工具声明的渲染源、脚本和图像，不分析任意JSON、任意程序或外部文件的所有依赖。manifest仍为可被整体替换的未签名本地清单，不认证出版来源或科学内容。
