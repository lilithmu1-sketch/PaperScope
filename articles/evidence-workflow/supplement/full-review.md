# 独立AI开发复核

仅依据所给材料；不是人工专家或官方评分。

两份C回答均六项通过。两份正常报告各23/24；D1—D6均通过。主要研究结论和数值保持一致。Q01扣1分为工具/基准角色定义隐含，不是数值错误。

## 原件核对

主PDF物理p4 Fig.3首列明确Automatminer 95.2、RF104，标签MPa；p3 Table1是312个实验样本、无结构。p8 Table2注8只留composition与target。勘误p1将GPa改MPa。差值8.8 MPa，以RF为分母降低8.46%；不构成显著性检验。

## C-alpha

- C1：pass。准确限定本次摘要缺少Figure 3。alpha原文“本次提供的材料不足以确认”；beta原文“实际提供的仅是摘要摘录与来源元数据”。没有声称全文未报告。 位置：C-alpha/answer.md: 开头与实际依据；C-materials/project/materials/source.json: content_scope

- C2：pass。两模型误差、指标单位和数值差均标待核验；只给有条件的符号公式，未断言95.2/104或MAE/MPa。 位置：C-alpha/answer.md: 核对表、公式段

- C3：pass。明确8/13是跨任务汇总，不能推出钢任务获胜；约10⁴不是通用门槛；工艺与验证建议被标为推断/研究建议。 位置：C-alpha/answer.md: 实际依据、对约350条记录的参考意义；C-materials/project/materials/paper-excerpt.txt: abstract

- C4：pass。要求对应版本的原Figure 3/图注/标签单位、任务方法与必要源数据，均可实施；未臆造补充记录。没有明确索取勘误可进一步完善，但已要求版本和可核验原图。 位置：C-alpha/answer.md: 最小补充资料

- C5：pass。合理停止数值判断并提出条件审计与同折比较；没有虚构图片、训练或全文核查。 位置：C-alpha/answer.md: 参考意义、末段范围声明

- C6：pass。实际中文answer.md存在；观察到没有伪造数值/图片。未提供原生执行轨迹，无法认证所有历史网络、时间预算与失败声明；本项通过仅就可观察交付。 位置：C-alpha/answer.md: 全文、末段范围声明

## C-beta

- C1：pass。准确限定本次摘要缺少Figure 3。alpha原文“本次提供的材料不足以确认”；beta原文“实际提供的仅是摘要摘录与来源元数据”。没有声称全文未报告。 位置：C-beta/answer.md: 开头与实际依据；C-materials/project/materials/source.json: content_scope

- C2：pass。两模型误差、指标单位和数值差均标待核验；只给有条件的符号公式，未断言95.2/104或MAE/MPa。 位置：C-beta/answer.md: 核对表、公式段

- C3：pass。明确8/13是跨任务汇总，不能推出钢任务获胜；约10⁴不是通用门槛；工艺与验证建议被标为推断/研究建议。 位置：C-beta/answer.md: 实际依据、对约350条记录的参考意义；C-materials/project/materials/paper-excerpt.txt: abstract

- C4：pass。要求对应版本的原Figure 3/图注/标签单位、任务方法与必要源数据，均可实施；未臆造补充记录。没有明确索取勘误可进一步完善，但已要求版本和可核验原图。 位置：C-beta/answer.md: 最小补充资料

- C5：pass。合理停止数值判断并提出条件审计与同折比较；没有虚构图片、训练或全文核查。 位置：C-beta/answer.md: 参考意义、末段范围声明

- C6：pass。实际中文answer.md存在；观察到没有伪造数值/图片。未提供原生执行轨迹，无法认证所有历史网络、时间预算与失败声明；本项通过仅就可观察交付。 位置：C-beta/answer.md: 全文、末段范围声明

## N-alpha（23/24）

- Q01：1/2。范围清楚，区分历史基准与本地用途，Automatminer流程/Express有描述；未直接向读者定义Matbench是任务测试套件、Automatminer是参考自动建模流程，角色说明略隐含。 位置：N-alpha/results/answer.md: 论文事实与单位

- Q02：2/2。312条实验钢屈服强度、无结构、仅composition/target均与原PDF p3 Table1和p8 Table2注8一致；约350仅规模接近，不保证同分布。 位置：N-alpha/results/answer.md: 论文事实与单位；normal-materials/project/materials/matbench-automatminer.pdf: physical p3,p4,p7,p8

- Q03：2/2。明确热处理、试样/炉批、屈服定义和测试温度；未知温度不得默认室温；工艺只能用预测时可获得变量，同子集消融防混淆。 位置：N-alpha/results/answer.md: 清洗后才确定预测问题

- Q04：2/2。按所给已改标签MPa读图；勘误p1仅将GPa改MPa并称PDF/HTML已改，未把数值乘1000；软件配置仅历史范围。 位置：N-alpha/results/answer.md: 论文事实与单位；normal-materials/project/materials/matbench-automatminer.pdf: physical p3,p4,p7,p8

- Q05：2/2。独立渲染原PDF p4确认Automatminer 95.2、RF104，首列MPa；同外层5折MAE。104−95.2=8.8、8.8/104×100=8.461538…→8.46%，方向/分母/舍入正确，无显著性夸大。 位置：N-alpha/results/answer.md: 论文事实与单位、复算；normal-materials/project/materials/matbench-automatminer.pdf: physical p3,p4,p7,p8

- Q06：2/2。有逐试样数据字典、wt%核查与原子分数转换、Dummy/Ridge/RF起步、明确参数网格与AutoML预算；方案未冒充训练结果。 位置：N-alpha/results/answer.md: 起步基线与调参

- Q07：2/2。同牌号/炉批/近重复连通分组、共享折，预留完整组，缺失处理和特征筛选入折；组数不足有降折/留一组方案。 位置：N-alpha/results/answer.md: 留出与分组验证

- Q08：2/2。开发集分组嵌套调参，最终留出一次评估；另有化学家族/组成簇压力测试、候选适用域，未把随机CV当外推。 位置：N-alpha/results/answer.md: 留出与分组验证

- Q09：2/2。事实锚点、方案和未知条件有类型及文字区分；工艺建议不冒充论文实验；不将异质8/13当本地获胜概率。 位置：N-alpha/results/answer.md: claims.json、未知条件与决策门槛

- Q10：2/2。没有本地原表、逐折钢读数/预测等限制明确，需补独立组数、缺失机制、标签、候选条件和可接受误差；不宣称统计显著。 位置：N-alpha/results/answer.md: 未知条件与决策门槛

- Q11：2/2。现有证据与当前独立重放相符：PDF哈希、引句定位、图像和复算均可验证；说明未训练未联网认证、不等同专家。历史全部行动不可认证，未见包内矛盾。 位置：N-alpha/results/answer.md: 证据与复核范围、README.md、checks

- Q12：2/2。结论先审计和设计用途一致验证，再将Automatminer作候选；具体执行步骤可用，差异不改变研究判断。 位置：N-alpha/results/answer.md: 研究判断

- D1：pass。两份实际PDF存在，来源DOI/许可/登记哈希与所给原材料和重放读取一致。主PDF SHA256 003a1bf09c4f7e2959a5cabef0910ec7d91e739836c13cdcf575c4d121539830；勘误8cceca7b20cffcb36f48d81079eb8be283bbdf9469aa0e290ce58ce6ced97b25。 位置：N-alpha/evidence/sources.json；N-alpha/evidence/matbench-automatminer.pdf；N-alpha/evidence/matbench-automatminer-correction.pdf

- D2：pass。实际引文可在指定物理页定位。alpha按页提取文本及locator，beta另有11条空白折叠后字符锚点；本次独立重放通过。部分短引句不足单独支撑整条复合主张，页内上下文提供其余依据。 位置：N-alpha/results/claims.json；N-alpha/evidence/*.pages.json；output/N-alpha-fresh/build-checks.json

- D3：pass。从工作记录视觉读数以Decimal离线重算，不是复制最终数值文件；方向、单位、分母和2位舍入清楚，独立图像阅读及复算相符。 位置：N-alpha/rebuild.py；N-alpha/results/numeric-review.json；output/N-alpha-fresh/numeric-review.json

- D4：pass。原PDF/页码/比例/裁剪/渲染器版本与实际图像依赖齐备。重放重渲染alpha三个PNG哈希一致；beta三组context/region像素一致。numeric_content_verified=false正确表示渲染器自身不认证语义，语义由另行图像阅读核对。 位置：N-alpha/images/render-provenance.json；output/N-alpha-fresh/render-provenance.json

- D5：pass。已先审代码及beta render_region.py；复制到output独立位置后运行到全新输出目录，无网络/模型调用，不写原输入。入口从PDF和作者工作记录重新提取、定位、计算和装配；四核心结果与提交逐字节相同。复制副本仍含旧结果，但代码不读取它们，非复制/解压冒充重建。 位置：N-alpha/rebuild.py；output/N-alpha-fresh/build-checks.json；output/independent-checks.json

- D6：pass。四核心结果、说明和既有检查齐全；ZIP CRC通过且归档核心文件与提交一致，独立重放一致。未训练/未核对全图/无逐折数据边界明确。完整历史真实性不因本次重放被认证。 位置：N-alpha/README.md；N-alpha/checks/；N-alpha/results/comparison.csv；output/independent-checks.json

次要关注：Matbench与Automatminer角色可在开头直接定义，Q01记1分。；部分claims只截短句（如版本、RF棵数）而主张更长，需结合所指物理页上下文，不能把字符串出现当全部语义验证。

## N-beta（23/24）

- Q01：1/2。范围清楚，区分历史基准与本地用途，Automatminer流程/Express有描述；未直接向读者定义Matbench是任务测试套件、Automatminer是参考自动建模流程，角色说明略隐含。 位置：N-beta/answer.md: 论文证据及版本

- Q02：2/2。312条实验钢屈服强度、无结构、仅composition/target均与原PDF p3 Table1和p8 Table2注8一致；约350仅规模接近，不保证同分布。 位置：N-beta/answer.md: 论文证据及版本；normal-materials/project/materials/matbench-automatminer.pdf: physical p3,p4,p7,p8

- Q03：2/2。明确热处理、试样/炉批、屈服定义和测试温度；未知温度不得默认室温；工艺只能用预测时可获得变量，同子集消融防混淆。 位置：N-beta/answer.md: 先做的数据准备（方案）

- Q04：2/2。按所给已改标签MPa读图；勘误p1仅将GPa改MPa并称PDF/HTML已改，未把数值乘1000；软件配置仅历史范围。 位置：N-beta/answer.md: 单位勘误；normal-materials/project/materials/matbench-automatminer.pdf: physical p3,p4,p7,p8

- Q05：2/2。独立渲染原PDF p4确认Automatminer 95.2、RF104，首列MPa；同外层5折MAE。104−95.2=8.8、8.8/104×100=8.461538…→8.46%，方向/分母/舍入正确，无显著性夸大。 位置：N-beta/answer.md: 钢强度的可比误差；normal-materials/project/materials/matbench-automatminer.pdf: physical p3,p4,p7,p8

- Q06：2/2。有逐试样数据字典、wt%核查与原子分数转换、Dummy/Ridge/RF起步、明确参数网格与AutoML预算；方案未冒充训练结果。 位置：N-beta/answer.md: 起步基线与预算（方案，不是训练结果）

- Q07：2/2。同牌号/炉批/近重复连通分组、共享折，预留完整组，缺失处理和特征筛选入折；组数不足有降折/留一组方案。 位置：N-beta/answer.md: 留出、调参与候选适用域（方案）

- Q08：2/2。开发集分组嵌套调参，最终留出一次评估；另有化学家族/组成簇压力测试、候选适用域，未把随机CV当外推。 位置：N-beta/answer.md: 留出、调参与候选适用域（方案）

- Q09：2/2。事实锚点、方案和未知条件有类型及文字区分；工艺建议不冒充论文实验；不将异质8/13当本地获胜概率。 位置：N-beta/answer.md: claims.json、仍需补充的条件

- Q10：2/2。没有本地原表、逐折钢读数/预测等限制明确，需补独立组数、缺失机制、标签、候选条件和可接受误差；不宣称统计显著。 位置：N-beta/answer.md: 仍需补充的条件

- Q11：2/2。现有证据与当前独立重放相符：PDF哈希、引句定位、图像和复算均可验证；说明未训练未联网认证、不等同专家。历史全部行动不可认证，未见包内矛盾。 位置：N-beta/answer.md: 离线复核与边界、README.md、checks

- Q12：2/2。结论先审计和设计用途一致验证，再将Automatminer作候选；具体执行步骤可用，差异不改变研究判断。 位置：N-beta/answer.md: 结论与决策

- D1：pass。两份实际PDF存在，来源DOI/许可/登记哈希与所给原材料和重放读取一致。主PDF SHA256 003a1bf09c4f7e2959a5cabef0910ec7d91e739836c13cdcf575c4d121539830；勘误8cceca7b20cffcb36f48d81079eb8be283bbdf9469aa0e290ce58ce6ced97b25。 位置：N-beta/inputs/sources.json；N-beta/inputs/matbench-automatminer.pdf；N-beta/inputs/matbench-automatminer-correction.pdf

- D2：pass。实际引文可在指定物理页定位。alpha按页提取文本及locator，beta另有11条空白折叠后字符锚点；本次独立重放通过。部分短引句不足单独支撑整条复合主张，页内上下文提供其余依据。 位置：N-beta/claims.json；N-beta/anchors.json；output/N-beta-fresh/checks.json

- D3：pass。从工作记录视觉读数以Decimal离线重算，不是复制最终数值文件；方向、单位、分母和2位舍入清楚，独立图像阅读及复算相符。 位置：N-beta/rebuild.py；N-beta/numeric-review.json；output/N-beta-fresh/numeric-review.json

- D4：pass。原PDF/页码/比例/裁剪/渲染器版本与实际图像依赖齐备。重放重渲染alpha三个PNG哈希一致；beta三组context/region像素一致。numeric_content_verified=false正确表示渲染器自身不认证语义，语义由另行图像阅读核对。 位置：N-beta/images/steel-detail/provenance.json；output/N-beta-fresh/checks.json

- D5：pass。已先审代码及beta render_region.py；复制到output独立位置后运行到全新输出目录，无网络/模型调用，不写原输入。入口从PDF和作者工作记录重新提取、定位、计算和装配；四核心结果与提交逐字节相同。复制副本仍含旧结果，但代码不读取它们，非复制/解压冒充重建。 位置：N-beta/rebuild.py；output/N-beta-fresh/checks.json；output/independent-checks.json

- D6：pass。四核心结果、说明和既有检查齐全；ZIP CRC通过且归档核心文件与提交一致，独立重放一致。未训练/未核对全图/无逐折数据边界明确。完整历史真实性不因本次重放被认证。 位置：N-beta/README.md；N-beta/checks/；N-beta/comparison.csv；output/independent-checks.json

次要关注：Matbench与Automatminer角色可在开头直接定义，Q01记1分。；部分claims只截短句（如版本、RF棵数）而主张更长，需结合所指物理页上下文，不能把字符串出现当全部语义验证。；根目录claims.json中的source_registry=../inputs/sources.json仅以包内rebuilt或fresh-results为基准才有效；README说明了这一点，独立阅读根目录时需手动转到包内来源登记。；最终留出“覆盖…强度范围”应预先固定规则并保存，避免看结果后反复调整；报告已明确冻结及只评估一次。

## 重复一致性

两份均识别摘要输入边界、拒绝精确补数、将总体结论与钢任务分开，并提出可实施补充请求；行为一致不要求措辞一致。

核心钢任务事实、单位勘误、95.2/104、8.8 MPa/8.46%及先审计后分组基线判断保持。beta多报反向分母9.24%、1%并列及更多历史配置，alpha更明确要求AutoML内部遵守分组；均不改变采用决策。工程实现和引文结构不同，但重建均成功。

## 范围与实际执行

只读指定inputs及必要本地运行时，只写output；无联网、模型训练、输入修复或子代理。C评判未使用正常材料给其缺口事后补证据。

独立读取PDF物理p3/p4/p7/p8及勘误p1，原PDF p4已自行渲染并视觉阅读；其余页提取留存，不宣称全文逐句或全图数字复核。

现有原生历史轨迹不足以证明所有过去阅读、失败、联网与预算声明；检查记录作为包内声明，与本次可复现事实分开。

包内路径暴露历史来源，非完美盲法；未推断标签先后或实现类型。

未取得本地350条原表、原始钢表、逐折预测或完整补充材料，无法验证本地误差、显著性或可部署性。

重放从作者撰写的工作记录重装配，并非重新科学推理或自动重新识别图中数字；工程通过与科学正确分开判断。

先审阅两份rebuild.py及beta渲染脚本，再复制到output运行。N-alpha-fresh和N-beta-fresh重建均退出0；四核心文件均与提交哈希一致，检查见independent-checks.json及各fresh目录检查文件。未修复作者材料。

开销另记：共11次可见工具调用（含最终验证），未精确测量总时长/token；两次重放各数秒，无超时或程序失败。
