# LogisticPilot 录制前产品与竞赛审查

## 产品判断

LogisticPilot 应继续聚焦小型零部件分销商：**到货出了问题，也不要让整张订单停下来。** 英文开场建议：**A receiving problem shouldn’t stop every order. LogisticPilot helps small distributors investigate the affected stock and keep eligible orders moving.**

当前最值得补的不是新功能数量，而是同一业务对象的连续性。Dashboard 上的问题必须能点进对应批次；Operations 必须说明该批次为什么待处理、影响哪张客户订单、下一步需要什么；Agent 的回答和操作结果必须能回到外部 ERP 单据核验。只有做到这一步，评委才容易把照片、对话、库存和发运看成一个产品，而不是几段独立演示。

现有可验证案例是 PO `PUR-ORD-2026-00025`、客户订单 `SAL-ORD-2026-00019`。25 件已收货，LOT-A20 的 20 件已经通过演示审批写入 ERP 发运，LOT-B5 的 5 件仍待检。这个结果来自实际演示租户，不代表物理配送或客户签收。照片模型给出的外观观察也不等于质量检验结论。[A1]

## 官方标准如何影响取舍

本届要求以 Strands 完成具体人的实际任务；五项标准等权，技术项优先用于同分比较。产品体验的完整性、具体受益人、可见业务结果和清晰的端到端展示都直接影响评分。视频最长五分钟；评委可以只看提交材料，所以视频必须独立讲清楚。运行链接或 AgentCore 有助技术项，但不能代替真实功能。多 agent 数量不是单独的评分项。[1]

提交前仍需核对公开仓库、许可证、架构图、英文材料、公开视频、免费测试入口及已有代码披露。当前 localhost 和私有运行配置不能自动等同于评委可用的测试入口。官方列出的科学家、工程师和开发者关系背景并不能证明他们偏爱某种 UI 或 agent 架构；以下建议是对标准和作品的分析，而非内部评审信息。[1][2]

## 竞争对手已经做了什么

| 参照 | 官方资料支持的能力 | 应借鉴的交互 | 不应作出的竞争主张 |
| --- | --- | --- | --- |
| Microsoft Dynamics 365 质量管理 | 质量单、非符合项、诊断与纠正任务、库存限制，以及历史质量指标。[3] | 问题必须绑定物料、数量、来源和处理任务；“查看问题”和“执行纠正”有明确边界。 | 不能说大厂只记录数据，不会处理异常。 |
| Microsoft Procurement Agent | 供应商变更的影响分析；按采购行查看下游订单和库存影响，摘要与明细分层，并能打开关联对象。当前查阅页面标为 production-ready preview。[4] | 固定显示正在分析哪一行物料；先给影响摘要，再展开数据；在上下文里完成审核。 | 不能说只有我们有 Agent、自动分析或跨订单影响。 |
| Oracle Quality Management | 检查与问题/纠正动作相连；动作可复制问题的附件和受影响对象，支持持续调查。[5][6] | 从一个具体问题进入流程，附件和对象关系随动作保留。 | 不能说质量闭环或整改管理本身是新发明。 |
| Oracle SCM AI Agents | 交易页面内嵌问答、基于上传政策和操作资料的上下文回答；Quality Inspection Advisor 处理检查标准相关咨询。[7] | Agent 跟随当前任务，减少在页面和文档间切换。 | 不能说交易内 Agent 侧栏或知识库咨询是独有能力。 |

这些材料并不能证明 Microsoft/Oracle 没有任何照片质检扩展，也没有建立所有套餐与价格的完整比较。**“他们做不到图像识别”与“我们比他们便宜多少”都不应进入录制台词。** 较可信的切口是为已有 ERPNext 的小团队做窄任务入口：少量界面操作，把图片线索、质量约束、可履约数量和外部记录接起来。安装成本、使用成本和用户节省时间仍需实际试点测量。

## 前届获奖作品能提供什么启发

本届尚未产生获奖结果。参照的是另一场 AWS AI Agent Global Hackathon；奖项由主办方公告确认，作品能力来自参赛者页面，未进行独立性能验证。[8]

| 作品 | 获奖事实与作品呈现 | 对本演示的启发 |
| --- | --- | --- |
| EcoLafaek | 前届第一名；从居民照片/GPS 报告进入污染分析、地图和工具驱动查询。[8][9] | 输入来自一个真实工作场景，输出成为可使用的业务对象。我们的照片必须关联具体批次，不能只是上传后多一段文字。 |
| Province | 前届第三名；对话收集资料、提取文档、完成税表，页面描述了专门分工和验证。[8][10] | 少问无关问题，让用户看到资料如何变成完成的工作。我们的终点应是订单状态和单据，而不是 Agent 说“建议发货”。 |
| AgentShell | 主办方确认最佳 Strands SDK 实现。[8] | 值得比较的是工具选择能否产生独立可观察的效果；不能仅凭奖项推断评委要求某个 agent 数量。 |

可借鉴的共同模式是“熟悉的任务 → 有理由的工具使用 → 可看见的结果”。这不是关于获奖原因的因果研究，也不支持用几个案例估算本项目获奖概率。

## 当前差距与录制优先级

| 优先级 | 发现 | 具体改进 | 验收依据 |
| --- | --- | --- | --- |
| P0 | Dashboard 的 Review hold 进入 Operations 顶部，问题批次不明显。 | 将真实 OPEN alert、lot、数量和订单保持在同一上下文；链接携带经当前案例校验的 lot。 | 点击 LOT-B5 的问题后，Operations 和 Agent 都显示 LOT-B5；后退/刷新不丢失选择。 |
| P0 | 外部单据有数据但入口隐藏，部分详情显示 JSON。 | ERP records 直接显示同一案例的原始单据链接、状态和 Check ERP。 | 打开真实 PO/DN/Shipment；重新 GET 后显示读回结果，不能只弹“成功”。 |
| P0 | 已完成发运和未解决质量问题容易混成“全部解决”。 | 案例总量 20 发运/5 待检，与 LOT-B5 的待检状态分开。 | 不把 LOT-A20 的发运算到 B5；不把 held 比例叫缺陷率。 |
| P1 | Agent 缺少当前批次简报，用户不知道问什么。 | 同一侧栏显示批次、受影响订单、缺失证据，并给三个上下文问题入口。 | 不自动跑付费模型；用户问题明确带当前批次，回答仍走真实 /assist。 |
| P1 | 展开后的检查区过窄，历史照片顺序和布局不利阅读。 | 当前批次相关照片优先，详情使用可用宽度，原始历史保留。 | 每个 disclosure 实际展开；无窄列长段、按钮溢出或读到一半收起。 |
| P1 | 常用演示/投稿文档仍指向旧 PO20、旧 Investigation 和旧发票场景。 | 当前故事与旧证据分开，明确主录制案例、输入和终点。 | 视频、说明、架构和单据不能跨案例拼成一个结果。 |
| P0，提交层面 | 免费评委访问和最终公开视频尚未验证。 | 完成实际访问与播放检查；不能拿 localhost 顶替。 | 此项独立于 UI 完成度，不因界面改完而自动通过。 |

## Agent 与 harness 应如何展示

当前 `/assist` 用真实 Strands/Bedrock 和结构化输出，可解释案例、追问缺失信息、请求图片分析或准备受支持的操作。其工具 `read_current_distributor_case` 返回应用预先读取的当前案例包；不能说每次工具调用又独立查询了所有外部系统。应用负责来源校验、数量、允许的动作、审批绑定和 ERP 回读。[A1][A2]

录制中应展示三个能改变工作进展的能力：看到图片却不擅自编出测量值；综合待检库存和订单约定解释可履约范围；人确认后能检查实际单据。界面里的 Review/Ask/Action/Verify 是业务步骤，不应伪装为运行了四个 agent。案例简报若由当前数据计算，明确作为案例状态展示，不冒充新生成的模型分析。

Strands 官方支持 hooks、Graph 和评估工具；这些能用于记录实际调用、约束执行和评价工具轨迹，但 SDK 有该功能不等于本条录制路径使用了它。[11][12][13] 历史 multi-agent/eval 结果可以作为附录，必须带原案例和日期；未完成的当前 Graph 对照不能宣传成准确率提升。眼下不值得为技术标签临时加一个无独立职责的 reviewer agent。

最小验收集合如下，预期结果在运行前固定，不喂给模型作为答案模板。它是同一 POC 的功能验收，不是统计 benchmark：

| 问题或操作 | 应观察到的行为 |
| --- | --- |
| Why is this lot held, and which order is affected? | 指向所选真实批次、质量依据、客户订单；不把照片当正式判废。 |
| Can the other stock move while this lot stays on hold? | 区分当前已发运与未发运状态，按当前合同/库存回答，不能重复承诺执行已完成动作。 |
| What evidence would let us release this lot? | 询问实际需要的测量/检查范围；不由外观无损推出合格。 |
| Check ERP / Open record | 刷新同一案例的来源并打开对应单据；不更改业务记录。 |
| 新照片未声明批次 | 需要时询问归属，不能随意绑定库存。 |

只对新改动涉及的行为做针对性检查；UI 由真实浏览器点击和人工审阅，不新增组件单元测试。每个实际模型调用记录问题、当前案例、输出和失败；不反复重跑直到得到漂亮答案，再隐藏失败。

## 业务价值怎样说才有力度

主数字建议是 **25 件中 20 件继续履约，5 件保持隔离**。80% 是这个案例的发运比例，不是质量良率、效率提升或客户收入增长。它让评委立即看到，处理异常不必导致所有合格库存一起等待。[A1]

邮费对比只作为决策权衡：示例采用 Medium Flat Rate Box 的 $24.80 公开零售价；两箱 $49.60 对一箱 $24.80，差额为 $24.80。合并装箱、重量、目的地和未来放行条件是 POC 假设。USPS 当前费率页面支持单箱数字，不支持这些货物确实能装下或已节约运费。[14] 本案选择先发 20 件，所以不能宣称已经省下合并寄送的差额。

演示可证明的价值是减少查找与切换、准确圈定待处理库存、让符合条件的订单推进。未来试点应测量每单人工触点、查证用时、正确升级率、未授权放行和重复单据。没有人工对照时，不把 Agent 延迟与某个猜测的人工工时相减作为 ROI。模拟历史趋势保留 Demo history 标签，也不能变成实际客户收益证据。

## 录制建议与获奖判断

以本轮修改前的 v9 界面和已核验记录作严格内部评分，五项各 5 分：

| 维度 | 暂评 | 拉低分数的主要原因 |
| --- | --- | --- |
| Technical Implementation | 3.5 | 真实 Strands、图片调用和 ERP 执行有证据；当前路径的自主多工具深度和可复现评委入口仍弱。 |
| Design | 2.5 | 已简洁，但问题批次、操作和外部记录之间的关系不明显；展开阅读会被刷新打断。 |
| Potential Impact | 3.0 | 小型分销商和部分履约结果具体；缺少真实使用者验证与人工对照。 |
| Creativity & Originality | 2.5 | 组合有实际用处；质量闭环、影响分析和内嵌 Agent 已有成熟竞争者。 |
| Presentation | 2.5 | 同一案例可演示，但现有脚本/投稿仍混有旧路径，视频顺序尚未冻结。 |

合计 **14/25**，只是用于排序工作的内部判断，不是 Devpost 评分或获奖预测。
本轮修补目标是消除已知扣分点；没有最终录屏和陌生观众审阅，不先把它改成“获奖级”高分。

推荐单一故事：仓库发现一批货有疑点，订单不能全部等着；操作员点入该批次，Agent 核对图片和库存，解释哪些能走、哪些还需检查；确认一个明确动作；打开 ERP 看到结果。视频只展示决定故事的少数展开区，其余展开区在排练时检查即可。

当前完成的 PO25 适合拍结果核验和剩余问题处理。要录制“待批准 → 确认 → 执行”的连续过程，必须使用新的隔离演示订单或明确呈现先前同一案例的原始录屏；不能重置前端数字冒充新执行。照片归属由操作员提供，A20 放行来自检查输入，B5 问题仍未关闭，三者必须讲清楚。

**判断：方向可参赛、有可辨认的 agent 工作，但不能因真实调用和较多工具就认定达到获奖级别。** 最大风险仍是陌生评委不能在几十秒内理解任务和看到结果，以及主录制路径没有证明多 agent 的增量价值。补齐上下文、外部单据与简短故事，会同时提升 Design、Impact 和 Presentation；它比新增 SaaS 标志或再做一套面板更值得投入。最终名次取决于整体作品与竞争者，没有可靠依据给获奖百分比。

## Sources

网页核对时间：2026-09-13 Pacific / 2026-09-14 UTC。产品预览文档可能变化；本报告不把 preview 当作已普遍部署。

1. Devpost/AWS. [Agents for Humans official rules](https://agentsforhumans.devpost.com/rules), updated August 12, 2026. Eligibility, criteria, video and test access.
2. Devpost/AWS. [Agents for Humans overview and judging panel](https://agentsforhumans.devpost.com/), accessed as above.
3. Microsoft Learn. [Quality and nonconformance management overview](https://learn.microsoft.com/en-us/dynamics365/supply-chain/inventory/quality-management-processes).
4. Microsoft Learn. [Review impact of purchase order changes from vendors](https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/procurement-agent-impact-analysis-review-changes), August 24, 2026, preview documentation.
5. Oracle. [About Working with Quality Issues and Actions](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fauqm/about-working-with-quality-issues-and-actions.html), 25D.
6. Oracle. [Manage Action Rules](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/fauqm/manage-action-rules.html), 25C.
7. Oracle. [Redwood: SCM AI Agents](https://docs.oracle.com/en/cloud/saas/readiness/scm/24d/ssproc24d/24D-ssproc-wn-f36341.htm), 24D; [SCM AI agents overview](https://www.oracle.com/scm/ai-agents-supply-chain-manufacturing/).
8. Devpost/AWS. [AWS AI Agent Global Hackathon winner announcement](https://aws-agent-hackathon.devpost.com/updates/38140-congratulations-to-the-winners-of-the-aws-ai-agent-global-hackathon).
9. EcoLafaek team. [Project submission](https://devpost.com/software/ecolafaek). Entrant claims.
10. Province author. [Project submission](https://devpost.com/software/province). Entrant claims.
11. Strands Agents. [Hooks](https://strandsagents.com/docs/user-guide/concepts/agents/hooks/).
12. Strands Agents. [Graph multi-agent pattern](https://strandsagents.com/docs/user-guide/concepts/multi-agent/graph/).
13. Strands Agents. [Evaluation SDK README](https://github.com/strands-agents/evals/blob/main/README.md).
14. USPS. [Notice 123, Priority Mail retail prices](https://pe.usps.com/text/dmm300/Notice123.htm).

A1. [Current contextual assistant and real ERP acceptance](../audits/2026-09-13-operations-assistant-acceptance.md).
A2. [Operations interaction review](../audits/2026-09-14-operations-interaction-review.md); current source implementation in `distributor_operations_assistant.py` and `distributor_operations.py`.
