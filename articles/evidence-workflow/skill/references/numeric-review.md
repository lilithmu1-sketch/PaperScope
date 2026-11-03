# 精确图表数值核验

需要报告精确数值、阈值或比较差异时使用；普通定性阅读无需强制增加附件。

1. 确定原始文件版本与SHA256，区分物理页码、印刷页码及图表编号。正文文本中出现相同数字，不能证明它属于所述指标。
2. 在整页上下文辨认图表、行列、单位、对数/归一化/误差条、脚注和实验条件。精确单元格需清楚可读；局部看不清时放大原PDF，不放大后自行补字。图像型PDF的原始像素不足时，放大也可能无效。
3. 阅读局部后再对照答案里的原始数值与比较方向，分别记录数据读数和自己计算的差异。派生量注明公式与原始值；未核查的值保持待核验。遇到冲突保留原记录，另记裁决依据；不悄悄改写实验回答。

## 可复现区域渲染

尚无可信坐标时，先生成整页和独立定位图：

```sh
python -B -X utf8 SKILL_DIR/scripts/render_region.py --pdf INPUT/paper.pdf --page 4 --overview --expected-sha256 REGISTERED_PDF_SHA256 --out OUT/new-overview
```

查看locator.png的0—1标尺定位图表，原页左/上为0、右/下为1，排除标尺图外围留白。locator包含新增网格与标尺，只用于定位；不要在它上面转录精确单元格或把它当未修改原图。未加标注的context.png和region.png为整页，provenance.json仍记录标准渲染出处；locator-provenance.json另记导航标注和哈希。导航文件不属于自动渲染依赖图的验证范围，只有实际需要审计导航过程时才作为普通附件显式归档。整页固定1.5倍渲染；--scale仅用于局部裁剪。

确定区域后可直接用原页比例裁剪，免去屏幕像素到PDF单位的手算：

```sh
python -B -X utf8 SKILL_DIR/scripts/render_region.py --pdf INPUT/paper.pdf --page 4 --rect-normalized 0.1 0.15 0.8 0.5 --scale 5 --expected-sha256 REGISTERED_PDF_SHA256 --out OUT/new-region
```

示例仅展示语法，实际区域须查看本次原页再选；保留行列名称、单位及必要图注，不能沿用其他论文坐标。provenance同时记录输入比例和换算后的PDF矩形；重渲染沿用后者。定位图不执行OCR或自动识别图表，也不能保证首次裁剪一定正确。

可选依赖：Python、pypdfium2及Pillow。开发验证环境使用pypdfium2 5.14.0，Pillow版本随每次渲染写入provenance.json。需要安装时使用当前环境的包管理器；本工具不联网、不自动安装。引文编译器不需要这些图像依赖。

```sh
python -B -X utf8 SKILL_DIR/scripts/render_region.py --pdf INPUT/paper.pdf --page 4 --rect 50 50 300 350 --scale 5 --expected-sha256 REGISTERED_PDF_SHA256 --out OUT/new-region-canvas
```

替换为实际路径、坐标和登记哈希；示例不指向特定论文答案。页码从1开始；坐标为未旋转显示页面左上角起的PDF画布单位，依次左、上、右、下。可先在PDF查看器或已有整页图上定位；像素坐标需除以其已知渲染比例，不能把屏幕像素直接当PDF坐标。矩形应尽量保留相关标签；输出还包括完整context.png供交叉阅读。默认不绘制注释，需检查批注时另用PDF查看器。

脚本拒绝覆盖、非有限/越界坐标、非法页码、源哈希不符及超过像素预算的渲染。旋转页面明确拒绝，改用PDF查看器并记录其旋转与坐标，不悄悄套用错误坐标。输出region.png、context.png及provenance.json；包含源与图片哈希、页码、矩形、渲染比例、库版本和脚本哈希。缺依赖或不能渲染时，改用可用查看器并披露实际方法；没有任何清楚原图时保留待核验。

provenance中的numeric_content_verified恒为false：它证明渲染出处，不证明阅读正确，更不会自动认证任何数字。

## 最小核验记录

对影响判断的已检查数值，记录实际值、对应答案位置、源SHA256、物理页/图表、行列、单位/条件、局部图出处、核验者类型及结果（已核对/待核验/冲突）。如在独立实验中使用，应按事前约定一致交付，不能事后只为某组补齐。它与字面引用报告分别保留，不将两者混为科学正确性认证。
